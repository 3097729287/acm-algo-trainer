use crate::{
    api::{ApiError, required_text},
    public_assets::AssetCache,
    storage::readonly,
};
use base64::{Engine, engine::general_purpose::STANDARD};
use rusqlite::{Connection, OptionalExtension, params};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, path::Path};

fn asset_reference(value: &Value) -> Option<&str> {
    value.as_str().and_then(|value| {
        value
            .strip_prefix("tb-asset:")
            .or_else(|| value.strip_prefix("/api/library-assets/"))
    })
}
pub fn asset_references(value: &Value) -> BTreeSet<String> {
    fn collect(value: &Value, found: &mut BTreeSet<String>) {
        for field in ["images", "archivedImages"] {
            if let Some(images) = value[field].as_object() {
                found.extend(
                    images
                        .values()
                        .filter_map(asset_reference)
                        .map(str::to_owned),
                );
            }
        }
        if let Some(attachments) = value["attachments"].as_object() {
            found.extend(
                attachments
                    .values()
                    .filter_map(|item| asset_reference(&item["data"]))
                    .map(str::to_owned),
            );
        }
        if let Some(sha) = asset_reference(&value["statementPdf"]["data"]) {
            found.insert(sha.into());
        }
        for field in ["translation", "detailedSolution"] {
            if value[field].is_object() {
                collect(&value[field], found);
            }
        }
        for method in value["methods"].as_array().into_iter().flatten() {
            collect(method, found);
        }
    }
    let mut found = BTreeSet::new();
    collect(value, &mut found);
    found
}

pub struct Library {
    pub db: Connection,
}
impl Library {
    pub fn open(path: &Path) -> Result<Self, ApiError> {
        let db = readonly(path)?;
        let count: i64 = db.query_row("SELECT count(*) FROM problems", [], |r| r.get(0))?;
        if count == 0 {
            return Err(ApiError::new(503, "LIBRARY_EMPTY", "内置题库缺失或为空"));
        }
        Ok(Self { db })
    }
    pub fn canonical(&self, id: &str) -> Result<String, ApiError> {
        if id.is_empty() || id.len() > 512 {
            return Err(ApiError::bad("题目编号无效"));
        }
        if let Some(found) = self
            .db
            .query_row("SELECT id FROM problems WHERE id=?", [id], |r| {
                r.get::<_, String>(0)
            })
            .optional()?
        {
            return Ok(found);
        }
        let found=self.db.query_row("SELECT id FROM problems WHERE EXISTS(SELECT 1 FROM json_each(encoded,'$.aliasIds') WHERE value=?1) LIMIT 1",[id],|r|r.get(0)).optional()?;
        found.ok_or_else(|| ApiError::missing("没有找到这道题，请刷新列表"))
    }
    pub fn row(&self, id: &str) -> Result<Value, ApiError> {
        let id = self.canonical(id)?;
        let raw: String =
            self.db
                .query_row("SELECT encoded FROM problems WHERE id=?", [id], |r| {
                    r.get(0)
                })?;
        Ok(serde_json::from_str(&raw)?)
    }
    pub fn statement(&self, id: &str) -> Result<Value, ApiError> {
        let mut value = self.statement_raw(id)?;
        self.hydrate(&mut value)?;
        Ok(value)
    }
    pub fn statement_raw(&self, id: &str) -> Result<Value, ApiError> {
        let row = self.row(id)?;
        let id = row["id"]
            .as_str()
            .ok_or_else(|| ApiError::new(500, "LIBRARY_RECORD", "题目索引格式异常"))?;
        let content: Option<String> = self
            .db
            .query_row(
                "SELECT content FROM statements WHERE problem_id=?",
                [id],
                |r| r.get(0),
            )
            .optional()?;
        let mut value = if let Some(content) = content {
            serde_json::from_str::<Value>(&content)?
        } else {
            json!({"markdown":null,"statementAvailable":false,"statementError":"题面尚未缓存"})
        };
        if !value.is_object() {
            return Err(ApiError::new(500, "LIBRARY_RECORD", "题面记录格式异常"));
        }
        let object = value.as_object_mut().unwrap();
        object.entry("id").or_insert(json!(id));
        object
            .entry("title")
            .or_insert_with(|| row["title"].clone());
        object.entry("url").or_insert_with(|| row["url"].clone());
        object.entry("samples").or_insert(json!([]));
        object
            .entry("limits")
            .or_insert(json!({"timeMs":2000,"memoryMb":256}));
        let sample_count = object["samples"].as_array().map_or(0, Vec::len);
        object
            .entry("judge")
            .or_insert(json!({"scope":"samples","label":"样例校验","cases":sample_count}));
        Ok(value)
    }
    pub fn solution(&self, id: &str) -> Result<Value, ApiError> {
        let id = self.canonical(id)?;
        let read = |table: &str| -> Result<Option<Value>, ApiError> {
            let value: Option<(String, String, String, String)> = self
                .db
                .query_row(
                    &format!(
                        "SELECT markdown,images,source_path,digest FROM {table} WHERE problem_id=?"
                    ),
                    [&id],
                    |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)),
                )
                .optional()?;
            value.map(|(markdown,images,path,digest)|Ok(json!({"markdown":markdown,"images":serde_json::from_str::<Value>(&images)?,"path":path,"digest":digest}))).transpose()
        };
        let base = read("solutions")?;
        let detailed = read("detailed_solutions")?;
        if base.is_none() && detailed.is_none() {
            return Err(ApiError::missing("这道题尚未收录题解"));
        }
        let row = self.row(&id)?;
        let mut result = base.unwrap_or(json!({"markdown":"","path":"","images":{},"digest":""}));
        result["title"] = row["title"].clone();
        result["url"] = row["url"].clone();
        result["detailedSolution"] = detailed.unwrap_or(Value::Null);
        let catalogue: Option<String> = self
            .db
            .query_row(
                "SELECT content FROM solution_methods WHERE problem_id=?",
                [&id],
                |r| r.get(0),
            )
            .optional()?;
        let catalogue: Value = match catalogue {
            Some(value) => serde_json::from_str(&value)?,
            None => json!({}),
        };
        let mut methods = Vec::new();
        for entry in catalogue["methods"].as_array().into_iter().flatten() {
            let mut method = entry.clone();
            let legacy = method
                .as_object_mut()
                .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "题解记录格式异常"))?
                .remove("legacy")
                == Some(json!(true));
            if legacy {
                let mut merged = result.clone();
                for (key, value) in method.as_object().unwrap() {
                    merged[key] = value.clone();
                }
                method = merged;
            }
            method
                .as_object_mut()
                .unwrap()
                .entry("images")
                .or_insert(json!({}));
            methods.push(method);
        }
        if methods.is_empty() {
            let mut method = result.clone();
            method["id"] = json!("original");
            method["title"] = json!("题解1");
            methods.push(method);
        }
        result["primaryMethod"] = catalogue
            .get("primaryMethod")
            .filter(|v| !v.is_null())
            .cloned()
            .unwrap_or_else(|| methods[0]["id"].clone());
        result["methods"] = json!(methods);
        Ok(result)
    }
    pub fn solution_summary(&self, id: &str) -> Result<Value, ApiError> {
        let exists:bool=self.db.query_row("SELECT EXISTS(SELECT 1 FROM solutions WHERE problem_id=?1) OR EXISTS(SELECT 1 FROM detailed_solutions WHERE problem_id=?1)",[id],|r|r.get(0))?;
        if !exists {
            return Ok(json!([]));
        }
        let raw: Option<String> = self
            .db
            .query_row(
                "SELECT content FROM solution_methods WHERE problem_id=?",
                [id],
                |r| r.get(0),
            )
            .optional()?;
        let catalog: Value = match raw {
            Some(v) => serde_json::from_str(&v)?,
            None => json!({}),
        };
        let methods = catalog["methods"]
            .as_array()
            .into_iter()
            .flatten()
            .map(|v| {
                v.as_object()
                    .unwrap()
                    .iter()
                    .filter(|(k, _)| ["id", "title", "supplemental"].contains(&k.as_str()))
                    .map(|(k, v)| (k.clone(), v.clone()))
                    .collect::<serde_json::Map<_, _>>()
            })
            .collect::<Vec<_>>();
        Ok(if methods.is_empty() {
            json!([{"id":"original","title":"题解1"}])
        } else {
            json!(methods)
        })
    }
    pub fn hydrate(&self, value: &mut Value) -> Result<(), ApiError> {
        self.hydrate_with(value, None)
    }
    pub fn hydrate_with(
        &self,
        value: &mut Value,
        derived: Option<&Connection>,
    ) -> Result<(), ApiError> {
        self.hydrate_with_cache(value, derived, None)
    }
    pub fn hydrate_with_cache(
        &self,
        value: &mut Value,
        derived: Option<&Connection>,
        cache: Option<&AssetCache>,
    ) -> Result<(), ApiError> {
        fn convert(
            library: &Library,
            value: &mut Value,
            derived: Option<&Connection>,
            cache: Option<&AssetCache>,
        ) -> Result<(), ApiError> {
            if let Some(sha) = asset_reference(value) {
                if sha.len() != 64 || !sha.bytes().all(|b| b.is_ascii_hexdigit()) {
                    return Err(ApiError::new(500, "ASSET_ID", "资源摘要无效"));
                }
                let asset = library.asset_bytes(sha, derived, cache)?;
                let Some((mime, data)) = asset else {
                    return Err(ApiError::new(
                        503,
                        "ASSET_NOT_CACHED",
                        "原始图片或 PDF 尚未缓存，请联网重试",
                    ));
                };
                *value = json!(format!("data:{mime};base64,{}", STANDARD.encode(data)));
            }
            Ok(())
        }
        for field in ["images", "archivedImages"] {
            if let Some(images) = value.get_mut(field).and_then(Value::as_object_mut) {
                for item in images.values_mut() {
                    convert(self, item, derived, cache)?;
                }
            }
        }
        if let Some(attachments) = value.get_mut("attachments").and_then(Value::as_object_mut) {
            for attachment in attachments.values_mut() {
                if let Some(data) = attachment.get_mut("data") {
                    convert(self, data, derived, cache)?;
                }
            }
        }
        if let Some(pdf) = value
            .get_mut("statementPdf")
            .and_then(|v| v.get_mut("data"))
        {
            convert(self, pdf, derived, cache)?;
        }
        for field in ["translation", "detailedSolution"] {
            if let Some(translation) = value.get_mut(field) {
                self.hydrate_with_cache(translation, derived, cache)?;
            }
        }
        if let Some(methods) = value.get_mut("methods").and_then(Value::as_array_mut) {
            for method in methods {
                self.hydrate_with_cache(method, derived, cache)?;
            }
        }
        Ok(())
    }
    /// Never performs network I/O. All remote bytes must be prefetched outside
    /// the service locks before domain writes can begin.
    pub fn asset_is_local(
        &self,
        sha: &str,
        derived: Option<&Connection>,
    ) -> Result<bool, ApiError> {
        if sha.len() != 64 || !sha.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Err(ApiError::bad("资源摘要无效"));
        }
        let exists: bool = self.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM statement_assets WHERE sha256=?)",
            [sha],
            |r| r.get(0),
        )?;
        if exists {
            return Ok(true);
        }
        match derived {
            Some(db) => Ok(db.query_row(
                "SELECT EXISTS(SELECT 1 FROM derived_assets WHERE sha256=?)",
                [sha],
                |r| r.get(0),
            )?),
            None => Ok(false),
        }
    }
    pub fn asset_bytes(
        &self,
        sha: &str,
        derived: Option<&Connection>,
        cache: Option<&AssetCache>,
    ) -> Result<Option<(String, Vec<u8>)>, ApiError> {
        if sha.len() != 64 || !sha.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Err(ApiError::bad("资源摘要无效"));
        }
        let inline: Option<(String, Vec<u8>)> = self
            .db
            .query_row(
                "SELECT mime,data FROM statement_assets WHERE sha256=?",
                [sha],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;
        let mut asset = match (inline, derived) {
            (Some(asset), _) => Some(asset),
            (None, Some(db)) => db
                .query_row(
                    "SELECT mime,data FROM derived_assets WHERE sha256=?",
                    [sha],
                    |r| Ok((r.get(0)?, r.get(1)?)),
                )
                .optional()?,
            _ => None,
        };
        if asset.is_none() {
            if let Some(cache) = cache {
                if let Some(descriptor) = cache.descriptor(&self.db, sha)? {
                    asset = cache
                        .read_cached(&descriptor)?
                        .map(|asset| (asset.mime, asset.data));
                }
            }
        }
        if asset
            .as_ref()
            .is_some_and(|(_, data)| format!("{:x}", Sha256::digest(data)) != sha)
        {
            return Err(ApiError::new(422, "ASSET_INTEGRITY", "原始资源校验失败"));
        }
        Ok(asset)
    }
    pub fn training_lists(&self) -> Result<Vec<Value>, ApiError> {
        let mut st = self
            .db
            .prepare_cached("SELECT content FROM training_lists ORDER BY rowid")?;
        st.query_map([], |r| r.get::<_, String>(0))?
            .map(|r| Ok(serde_json::from_str(&r?)?))
            .collect()
    }
    pub fn lecture(&self, id: &str) -> Result<Value, ApiError> {
        let content: String =
            self.db
                .query_row("SELECT content FROM lectures WHERE id=?", [id], |r| {
                    r.get(0)
                })?;
        Ok(serde_json::from_str(&content)?)
    }
    pub fn lectures(&self) -> Result<Value, ApiError> {
        let mut st = self
            .db
            .prepare_cached("SELECT content FROM lectures ORDER BY rowid")?;
        let mut rows = Vec::new();
        for content in st.query_map([], |r| r.get::<_, String>(0))? {
            let mut row: Value = serde_json::from_str(&content?)?;
            // Never transfer full article bodies just to render the directory.
            if let Some(object) = row.as_object_mut() {
                object.remove("markdown");
                object.remove("images");
            }
            rows.push(row);
        }
        Ok(json!({"lectures":rows}))
    }
    pub fn lectures_for_problem(&self, id: &str) -> Result<Value, ApiError> {
        let mut st=self.db.prepare_cached("SELECT l.content,pl.kind FROM problem_lectures pl JOIN lectures l ON l.id=pl.lecture_id WHERE pl.problem_id=? ORDER BY pl.position")?;
        let mut result = Vec::new();
        let mut seen = std::collections::HashSet::new();
        for row in st.query_map([id], |r| {
            Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?))
        })? {
            let (content, kind) = row?;
            let mut value: Value = serde_json::from_str(&content)?;
            let digest = Sha256::digest(value["markdown"].as_str().unwrap_or("").as_bytes());
            if !seen.insert(digest) {
                continue;
            }
            let object = value
                .as_object_mut()
                .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "讲义记录格式异常"))?;
            for field in ["images", "sourceMarkdown", "markdown", "sourceCodeHashes"] {
                object.remove(field);
            }
            value["referenceKind"] = json!(kind);
            result.push(value);
        }
        Ok(json!(result))
    }
    pub fn asset(&self, sha256: &str) -> Result<Value, ApiError> {
        self.asset_with_cache(sha256, None, None)
    }
    pub fn asset_with_cache(
        &self,
        sha256: &str,
        derived: Option<&Connection>,
        cache: Option<&AssetCache>,
    ) -> Result<Value, ApiError> {
        let (mime, data) = self
            .asset_bytes(sha256, derived, cache)?
            .ok_or_else(|| ApiError::missing("原始资源尚未收录"))?;
        Ok(json!({"sha256":sha256,"mime":mime,"bytes":data.len(),"data":STANDARD.encode(data)}))
    }
    pub fn page(&self, query: &Value) -> Result<Value, ApiError> {
        let offset = query.get("offset").and_then(Value::as_u64).unwrap_or(0);
        let limit = query.get("limit").and_then(Value::as_u64).unwrap_or(100);
        if limit == 0 || limit > 500 || offset > i32::MAX as u64 {
            return Err(ApiError::bad("分页参数无效"));
        }
        let search = query.get("q").and_then(Value::as_str).unwrap_or("");
        if search.len() > 800 {
            return Err(ApiError::bad("搜索内容过长"));
        }
        let total: i64 = self.db.query_row(
            "SELECT count(*) FROM problems WHERE ?1='' OR instr(lower(encoded),lower(?1))>0",
            [search],
            |r| r.get(0),
        )?;
        let mut st=self.db.prepare_cached("SELECT encoded FROM problems WHERE ?1='' OR instr(lower(encoded),lower(?1))>0 ORDER BY rowid LIMIT ?2 OFFSET ?3")?;
        let rows = st
            .query_map(params![search, limit as i64, offset as i64], |r| {
                r.get::<_, String>(0)
            })?
            .map(|r| Ok(serde_json::from_str::<Value>(&r?)?))
            .collect::<Result<Vec<_>, ApiError>>()?;
        let has_more = offset + (rows.len() as u64) < total as u64;
        Ok(json!({"rows":rows,"total":total,"offset":offset,"limit":limit,"hasMore":has_more}))
    }
    pub fn validate_id(&self, body: &Value) -> Result<String, ApiError> {
        self.canonical(required_text(body, "id", 512)?)
    }
}

pub fn wiki(path: &Path, query: &str, id: Option<&str>) -> Result<Value, ApiError> {
    let db = readonly(path)?;
    let meta = |key: &str| -> Result<String, ApiError> {
        Ok(
            db.query_row("SELECT value FROM metadata WHERE key=?", [key], |r| {
                r.get(0)
            })?,
        )
    };
    let captured = meta("capturedAt")?;
    if let Some(id) = id {
        let row=db.query_row("SELECT id,title,category,url,revision,sha256,html FROM articles WHERE id=?",[id],|r|Ok(json!({"id":r.get::<_,String>(0)?,"title":r.get::<_,String>(1)?,"category":r.get::<_,String>(2)?,"url":r.get::<_,String>(3)?,"revision":r.get::<_,String>(4)?,"sha256":r.get::<_,String>(5)?,"html":r.get::<_,String>(6)?})))?;
        return Ok(json!({"article":row,"capturedAt":captured}));
    }
    if query.chars().count() > 200 {
        return Err(ApiError::bad("搜索内容过长"));
    }
    let terms = query
        .to_lowercase()
        .split_whitespace()
        .map(String::from)
        .collect::<Vec<_>>();
    let mut st =
        db.prepare("SELECT id,title,category,url,search_text FROM articles ORDER BY rowid")?;
    let mut rows = Vec::new();
    let candidates = st.query_map([], |r| {
        Ok((
            r.get::<_, String>(0)?,
            r.get::<_, String>(1)?,
            r.get::<_, String>(2)?,
            r.get::<_, String>(3)?,
            r.get::<_, String>(4)?,
        ))
    })?;
    for candidate in candidates {
        let (id, title, category, url, text) = candidate?;
        let searchable = format!("{title} {text}").to_lowercase();
        if terms.iter().all(|term| searchable.contains(term)) {
            rows.push(json!({"id":id,"title":title,"category":category,"url":url}));
        }
    }
    Ok(json!({"articles":rows,"revision":meta("revision")?,"capturedAt":captured}))
}
