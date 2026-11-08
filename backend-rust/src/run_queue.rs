//! Two bounded native workers, with durable immutable run records.
use crate::{
    ApiError,
    api::now,
    native_judge::{self, RunPlan, Toolchains},
    storage::PersonalStore,
};
use chrono::{DateTime, Utc};
use rusqlite::params;
use serde_json::{Value, json};
use std::{
    collections::HashMap,
    fs::{File, OpenOptions},
    path::{Path, PathBuf},
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread::{self, JoinHandle},
};

struct State {
    closed: AtomicBool,
    pending_write: AtomicBool,
    failed: Mutex<HashMap<String, (String, Value, String)>>,
    jobs: Mutex<HashMap<String, Arc<AtomicBool>>>,
}
pub struct Reservation {
    pub id: String,
    cancel: Arc<AtomicBool>,
    state: Arc<State>,
}
impl Drop for Reservation {
    fn drop(&mut self) {
        if let Ok(mut jobs) = self.state.jobs.lock() {
            jobs.remove(&self.id);
        }
    }
}
pub struct RunQueue {
    state: Arc<State>,
    handles: Mutex<Vec<JoinHandle<()>>>,
    tools: Toolchains,
    work: PathBuf,
    _workspace_lease: File,
}
fn unavailable() -> ApiError {
    ApiError::new(
        503,
        "RUNNER_UNAVAILABLE",
        "本机运行服务暂时不可用，代码已保留",
    )
}

impl RunQueue {
    pub fn open(
        path: &Path,
        tools: Toolchains,
        owner: &str,
        store: &mut PersonalStore,
    ) -> Result<Self, ApiError> {
        let mut options = OpenOptions::new();
        options.read(true).write(true).create(true).truncate(false);
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt;
            options.share_mode(0);
        }
        let lease = options
            .open(path.with_extension("native-run.lock"))
            .map_err(|_| {
                ApiError::new(
                    409,
                    "RUNNER_WORKSPACE_BUSY",
                    "原生工作区已在另一个窗口打开，请先关闭原窗口",
                )
            })?;
        Self::recover(store, owner)?;
        Ok(Self {
            state: Arc::new(State {
                closed: AtomicBool::new(false),
                pending_write: AtomicBool::new(false),
                failed: Mutex::new(HashMap::new()),
                jobs: Mutex::new(HashMap::new()),
            }),
            handles: Mutex::new(vec![]),
            tools,
            work: path.parent().unwrap_or(Path::new(".")).join("native-runs"),
            _workspace_lease: lease,
        })
    }
    fn recover(store: &mut PersonalStore, owner: &str) -> Result<(), ApiError> {
        let records = store.rows(
            "SELECT key,value FROM account_preferences WHERE key LIKE 'native-run:%'",
            [],
        )?;
        for record in records.as_array().unwrap() {
            let marker: Value =
                serde_json::from_str(record["value"].as_str().ok_or_else(unavailable)?)?;
            if marker["owner"] != owner {
                continue;
            }
            if marker["schema"] != 1 {
                return Err(ApiError::pending());
            }
            let id = record["key"]
                .as_str()
                .unwrap()
                .strip_prefix("native-run:")
                .unwrap();
            let pending:bool=store.db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE id=? AND finished_at IS NULL AND mode='run' AND scope='samples')",[id],|row|row.get(0))?;
            if pending {
                let outcome = json!({"verdict":"ERROR","message":"上次本地运行已中断，原代码和输入已保留，请手动重新运行","passed":0,"total":0,"output":"","stderr":"","caseResults":[],"timeMs":null,"memoryKb":null});
                Self::finish(store, id, owner, &outcome, &now())?;
            }
        }
        Ok(())
    }
    pub fn validate_tools(&self, language: &str) -> Result<(), ApiError> {
        self.tools.executable(language).map(|_| ())
    }
    pub fn reserve(&self) -> Result<Reservation, ApiError> {
        let mut jobs = self.state.jobs.lock().map_err(|_| unavailable())?;
        if self.state.closed.load(Ordering::Acquire) || self.has_pending_write() {
            return Err(unavailable());
        }
        if jobs.len() >= 2 {
            return Err(ApiError::new(
                429,
                "RUNNER_BUSY",
                "已有两个本地任务正在运行，请等待完成",
            ));
        }
        let id = format!("submission-{}", uuid::Uuid::new_v4().simple());
        let cancel = Arc::new(AtomicBool::new(false));
        jobs.insert(id.clone(), Arc::clone(&cancel));
        Ok(Reservation {
            id,
            cancel,
            state: Arc::clone(&self.state),
        })
    }
    pub fn launch(
        &self,
        reservation: Reservation,
        plan: RunPlan,
        store: Arc<Mutex<PersonalStore>>,
        owner: String,
        clock: Option<DateTime<Utc>>,
    ) -> Result<(), ApiError> {
        let tools = self.tools.clone();
        let work = self.work.clone();
        let id = reservation.id.clone();
        let error_store = Arc::clone(&store);
        let error_owner = owner.clone();
        let error_id = id.clone();
        let worker=thread::Builder::new().name("tobe-local-run".into()).spawn(move|| {
            let outcome=std::panic::catch_unwind(std::panic::AssertUnwindSafe(||native_judge::evaluate(&plan,&tools,&work,&reservation.cancel)));
            let outcome=match outcome {Ok(Ok(value))=>value,Ok(Err(error))=>json!({"verdict":"ERROR","message":error.message}),Err(_)=>json!({"verdict":"ERROR","message":"本次本地运行未完成，原代码和输入已保留"})};
            let stamp=clock.unwrap_or_else(Utc::now).to_rfc3339_opts(chrono::SecondsFormat::Micros,true);
            let saved=store.lock().map_err(|_|unavailable()).and_then(|mut store|Self::finish(&mut store,&id,&owner,&outcome,&stamp));
            if saved.is_err() {
                if let Ok(mut failed)=reservation.state.failed.lock() {
                    failed.insert(id,(owner,outcome,stamp));
                    reservation.state.pending_write.store(true,Ordering::Release);
                }
            }
            drop(reservation);
        });
        match worker {
            Ok(handle) => {
                let mut handles = self.handles.lock().map_err(|_| unavailable())?;
                let mut active = vec![];
                for previous in handles.drain(..) {
                    if previous.is_finished() {
                        let _ = previous.join();
                    } else {
                        active.push(previous);
                    }
                }
                active.push(handle);
                *handles = active;
                Ok(())
            }
            Err(_) => {
                if let Ok(mut store) = error_store.lock() {
                    Self::finish(
                        &mut store,
                        &error_id,
                        &error_owner,
                        &json!({"verdict":"ERROR","message":"本机运行任务未能启动，原代码和输入已保留"}),
                        &now(),
                    )?;
                }
                Err(unavailable())
            }
        }
    }
    pub fn has_pending_write(&self) -> bool {
        self.state.pending_write.load(Ordering::Acquire)
    }
    pub fn flush_pending(&self, store: &mut PersonalStore) -> Result<(), ApiError> {
        let mut failed = self.state.failed.lock().map_err(|_| unavailable())?;
        let mut saved = vec![];
        for (id, (owner, outcome, stamp)) in failed.iter() {
            Self::finish(store, id, owner, outcome, stamp)?;
            saved.push(id.clone());
        }
        for id in saved {
            failed.remove(&id);
        }
        self.state
            .pending_write
            .store(!failed.is_empty(), Ordering::Release);
        Ok(())
    }
    fn finish(
        store: &mut PersonalStore,
        id: &str,
        owner: &str,
        outcome: &Value,
        stamp: &str,
    ) -> Result<(), ApiError> {
        let key = format!("native-run:{id}");
        let mut marker = store.document(&key)?.ok_or_else(unavailable)?;
        if marker["schema"] != 1 || marker["owner"] != owner {
            return Err(ApiError::new(
                409,
                "ACCOUNT_CHANGED",
                "运行任务所属账号已变化，原记录已保留",
            ));
        }
        let verdict = outcome["verdict"]
            .as_str()
            .filter(|v| {
                [
                    "SAMPLE_PASS",
                    "RUN_OK",
                    "WA",
                    "TLE",
                    "MLE",
                    "OLE",
                    "RE",
                    "CE",
                    "ERROR",
                ]
                .contains(v)
            })
            .unwrap_or("ERROR");
        let tx = store.db.transaction()?;
        let changed=tx.execute("UPDATE submissions SET finished_at=?,verdict=?,time_ms=?,memory_kb=?,passed=?,total=?,output=?,stderr=?,message=?,case_results=? WHERE id=? AND finished_at IS NULL AND mode='run' AND scope='samples'",params![stamp,verdict,outcome["timeMs"].as_f64(),outcome["memoryKb"].as_u64().map(|v|v as i64),outcome["passed"].as_u64().unwrap_or(0) as i64,outcome["total"].as_u64().unwrap_or(0) as i64,outcome["output"].as_str().unwrap_or(""),outcome["stderr"].as_str().unwrap_or(""),outcome["message"].as_str().unwrap_or(""),outcome.get("caseResults").cloned().unwrap_or(json!([])).to_string(),id])?;
        if changed == 1 {
            marker["status"] = "finished".into();
            PersonalStore::put(&tx, &key, &marker.to_string(), stamp)?;
        }
        tx.commit()?;
        Ok(())
    }
    pub fn shutdown(&self) {
        self.state.closed.store(true, Ordering::Release);
        if let Ok(jobs) = self.state.jobs.lock() {
            for cancel in jobs.values() {
                cancel.store(true, Ordering::Release);
            }
        }
        let handles = self
            .handles
            .lock()
            .map(|mut handles| std::mem::take(&mut *handles))
            .unwrap_or_default();
        for handle in handles {
            let _ = handle.join();
        }
    }
}
impl Drop for RunQueue {
    fn drop(&mut self) {
        self.shutdown();
    }
}
