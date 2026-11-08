//! Immutable public projection compiled from the reviewed content at build time.
//! Personal facts never enter this database. SQL indexes resolve legacy aliases.
use crate::{
    api::{ApiError, today},
    storage::{PersonalStore, readonly},
};
use rusqlite::{Connection, OptionalExtension};
use serde_json::{Value, json};
use std::io::Read;
use std::path::Path;

pub struct Catalogue {
    pub db: Connection,
}
impl Catalogue {
    pub fn open(path: &Path, library: &Connection) -> Result<Self, ApiError> {
        let db = readonly(path)?;
        let result = Self { db };
        if result.meta("format")? != json!(4) {
            return Err(ApiError::new(
                409,
                "CATALOGUE_VERSION",
                "题库索引版本不兼容",
            ));
        }
        let source = result.meta("source")?;
        for key in ["schema", "revision"] {
            let actual: String =
                library.query_row("SELECT value FROM library_meta WHERE key=?", [key], |r| {
                    r.get(0)
                })?;
            if source[key] != actual {
                return Err(ApiError::new(
                    409,
                    "CATALOGUE_STALE",
                    "题库已变化，请重新构建目录索引",
                ));
            }
        }
        let actual: (String, i64) = library.query_row(
            "SELECT identity,generation FROM catalog_generation WHERE id=1",
            [],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
        if source["generation"] != json!([actual.0, actual.1]) {
            return Err(ApiError::new(
                409,
                "CATALOGUE_STALE",
                "题库已变化，请重新构建目录索引",
            ));
        }
        Ok(result)
    }
    pub fn meta(&self, key: &str) -> Result<Value, ApiError> {
        let raw: String =
            self.db
                .query_row("SELECT value FROM metadata WHERE key=?", [key], |r| {
                    r.get(0)
                })?;
        Ok(serde_json::from_str(&raw)?)
    }
    pub fn canonical(&self, id: &str) -> Result<Option<String>, ApiError> {
        Ok(self
            .db
            .query_row("SELECT canonical FROM aliases WHERE id=?", [id], |r| {
                r.get(0)
            })
            .optional()?)
    }
    pub fn equivalent(&self, id: &str) -> Result<Vec<String>, ApiError> {
        let canonical = self.canonical(id)?.unwrap_or_else(|| id.into());
        let mut st = self
            .db
            .prepare_cached("SELECT id FROM aliases WHERE canonical=? ORDER BY id")?;
        let mut ids = st
            .query_map([&canonical], |r| r.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?;
        if !ids.iter().any(|v| v == id) {
            ids.push(id.into());
            ids.sort();
        }
        Ok(ids)
    }
    pub fn row(&self, id: &str, compact: bool) -> Result<Option<Value>, ApiError> {
        let id = self.canonical(id)?.unwrap_or_else(|| id.into());
        let field = if compact { "compact" } else { "full" };
        if compact {
            let raw: Option<String> = self
                .db
                .query_row(
                    &format!("SELECT {field} FROM catalogue WHERE id=?"),
                    [id],
                    |r| r.get(0),
                )
                .optional()?;
            raw.map(|v| serde_json::from_str(&v).map_err(Into::into))
                .transpose()
        } else {
            let raw: Option<Vec<u8>> = self
                .db
                .query_row("SELECT full FROM catalogue WHERE id=?", [id], |r| r.get(0))
                .optional()?;
            raw.map(|v| decode(&v)).transpose()
        }
    }
    pub fn problem_projection(&self, id: &str, base: &mut Value) -> Result<Value, ApiError> {
        let (patch, knowledge, error): (Vec<u8>, Vec<u8>, Option<String>) = self.db.query_row(
            "SELECT patch,knowledge,error FROM problem_projections WHERE id=?",
            [id],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )?;
        if error.is_some() {
            return Err(ApiError::new(
                503,
                "STATEMENT_NOT_READY",
                "这道题的原始资源尚未完整缓存，请先使用当前正式版",
            ));
        }
        let patches = decode(&patch)?;
        for patch in patches
            .as_array()
            .ok_or_else(|| ApiError::new(500, "CATALOGUE_RECORD", "题面投影格式异常"))?
        {
            let path = patch["path"]
                .as_array()
                .filter(|p| !p.is_empty())
                .ok_or_else(|| ApiError::new(500, "CATALOGUE_RECORD", "题面投影格式异常"))?;
            let mut parent = &mut *base;
            for field in &path[..path.len() - 1] {
                let field = field
                    .as_str()
                    .ok_or_else(|| ApiError::new(500, "CATALOGUE_RECORD", "题面投影格式异常"))?;
                parent = parent.get_mut(field).ok_or_else(|| {
                    ApiError::new(500, "CATALOGUE_RECORD", "题面投影与原始内容不匹配")
                })?;
            }
            let field = path
                .last()
                .and_then(Value::as_str)
                .ok_or_else(|| ApiError::new(500, "CATALOGUE_RECORD", "题面投影格式异常"))?;
            if patch["remove"] == true {
                parent
                    .as_object_mut()
                    .ok_or_else(|| ApiError::new(500, "CATALOGUE_RECORD", "题面投影格式异常"))?
                    .remove(field);
            } else {
                parent[field] = patch["value"].clone();
            }
        }
        decode(&knowledge)
    }
    pub fn data(&self, compact: bool, token: &str) -> Result<Value, ApiError> {
        let field = if compact { "compact" } else { "full" };
        let mut st = self
            .db
            .prepare_cached(&format!("SELECT {field} FROM catalogue ORDER BY position"))?;
        let rows = if compact {
            st.query_map([], |r| r.get::<_, String>(0))?
                .map(|v| Ok(serde_json::from_str::<Value>(&v?)?))
                .collect::<Result<Vec<_>, ApiError>>()?
        } else {
            st.query_map([], |r| r.get::<_, Vec<u8>>(0))?
                .map(|v| decode(&v?))
                .collect::<Result<Vec<_>, ApiError>>()?
        };
        Ok(
            json!({"rows":rows,"statuses":self.meta("statuses")?,"categories":self.meta("categories")?,"revision":self.meta("revision")?,"today":today(),"token":token}),
        )
    }
    pub fn review_knowledge(&self, id: &str) -> Result<Value, ApiError> {
        let available:bool=self.db.query_row("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='review_knowledge')",[],|row|row.get(0))?;
        if !available {
            return Err(ApiError::pending());
        }
        if self.meta("reviewKnowledgeVersion")? != json!(1) {
            return Err(ApiError::pending());
        }
        let (content, error): (Vec<u8>, Option<String>) = self.db.query_row(
            "SELECT content,error FROM review_knowledge WHERE id=?",
            [id],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )?;
        if error.is_some() {
            return Err(ApiError::new(
                503,
                "STATEMENT_NOT_READY",
                "这道题的原始资源尚未完整缓存，请先使用当前正式版",
            ));
        }
        decode(&content)
    }
    pub fn lectures(
        &self,
        personal: &PersonalStore,
        curriculum: &Value,
        library: &Connection,
    ) -> Result<Value, ApiError> {
        let mut st = self
            .db
            .prepare_cached("SELECT content FROM lecture_summaries ORDER BY position")?;
        let rows = st
            .query_map([], |r| r.get::<_, String>(0))?
            .map(|v| Ok(serde_json::from_str::<Value>(&v?)?))
            .collect::<Result<Vec<_>, ApiError>>()?;
        let reached=personal.rows("SELECT identity FROM(SELECT id AS identity,active_at AS stamp FROM training UNION ALL SELECT problem_id,saved_at FROM drafts UNION ALL SELECT problem_id,submitted_at FROM submissions) GROUP BY identity ORDER BY MIN(stamp),identity",[])?;
        let mut encountered = Vec::<String>::new();
        for reached in reached.as_array().unwrap() {
            let mut references = library.prepare_cached(
                "SELECT lecture_id FROM problem_lectures WHERE problem_id=? ORDER BY position",
            )?;
            for id in references.query_map([reached["identity"].as_str().unwrap_or("")], |r| {
                r.get::<_, String>(0)
            })? {
                let id = id?;
                if !encountered.contains(&id) {
                    encountered.push(id);
                }
            }
        }
        let mut lessons = curriculum["lessons"]
            .as_array()
            .cloned()
            .unwrap_or_default();
        lessons.sort_by_key(|v| v["order"].as_i64().unwrap_or(0));
        let foundation = lessons
            .iter()
            .filter(|v| v["kind"] == "language")
            .map(|v| v["id"].clone())
            .collect::<Vec<_>>();
        for row in &rows {
            if row["sourceProblemIds"].as_array().is_some_and(|ids| {
                ids.iter().any(|id| {
                    reached
                        .as_array()
                        .unwrap()
                        .iter()
                        .any(|r| r["identity"] == *id)
                })
            }) {
                let id = row["id"].as_str().unwrap_or("").to_owned();
                if !encountered.contains(&id) {
                    encountered.push(id);
                }
            }
        }
        Ok(
            json!({"lectures":rows,"revision":self.meta("lectureRevision")?,"curationVersion":self.meta("curationVersion")?,"audit":{"lectureCount":rows.len(),"usingDatabase":true,"exceptionCount":0},"learningQueue":{"version":1,"foundationIds":foundation,"encounteredIds":encountered}}),
        )
    }
    pub fn training_lists(
        &self,
        personal: &PersonalStore,
        custom_only: bool,
    ) -> Result<Value, ApiError> {
        let mut lists = Vec::new();
        if !custom_only {
            let mut st = self
                .db
                .prepare_cached("SELECT content FROM training_lists ORDER BY position")?;
            for raw in st.query_map([], |r| r.get::<_, String>(0))? {
                lists.push(serde_json::from_str::<Value>(&raw?)?);
            }
        }
        lists.extend(crate::custom_lists::read(personal)?);
        Ok(json!({"lists":lists}))
    }

    pub fn replay_events(&self, personal: &PersonalStore) -> Result<Value, ApiError> {
        let private: bool = personal.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM account_problem_facts)",
            [],
            |row| row.get(0),
        )?;
        if private {
            return Err(ApiError::pending());
        }
        let raw: Option<String> = self
            .db
            .query_row(
                "SELECT value FROM metadata WHERE key='replayEvents'",
                [],
                |row| row.get(0),
            )
            .optional()?;
        let value: Value = serde_json::from_str(&raw.ok_or_else(ApiError::pending)?)?;
        if !value["events"].is_array() {
            return Err(ApiError::new(
                422,
                "CATALOGUE_FORMAT",
                "比赛目录数据格式异常",
            ));
        }
        Ok(value)
    }
}
fn decode(raw: &[u8]) -> Result<Value, ApiError> {
    let mut data = Vec::new();
    flate2::read::ZlibDecoder::new(raw)
        .take(8 * 1024 * 1024 + 1)
        .read_to_end(&mut data)?;
    if data.len() > 8 * 1024 * 1024 {
        return Err(ApiError::new(422, "CATALOGUE_LIMIT", "单题元数据超过限制"));
    }
    Ok(serde_json::from_slice(&data)?)
}

pub fn row_or_portable(
    catalogue: &Catalogue,
    personal: &PersonalStore,
    id: &str,
) -> Result<Value, ApiError> {
    if let Some(row) = catalogue.row(id, true)? {
        return Ok(row);
    }
    let fact: Option<String> = personal
        .db
        .query_row(
            "SELECT value FROM account_problem_facts WHERE problem_id=?",
            [id],
            |r| r.get(0),
        )
        .optional()?;
    if let Some(fact) = fact {
        let fact: Value = serde_json::from_str(&fact)?;
        if fact.get("row").is_some_and(Value::is_object) {
            return Ok(fact["row"].clone());
        }
    }
    Err(ApiError::missing("没有找到这道题，请刷新列表"))
}
