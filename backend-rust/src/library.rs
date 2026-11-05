use crate::{
    api::{ApiError, required_text},
    storage::readonly,
};
use base64::{Engine, engine::general_purpose::STANDARD};
use rusqlite::{Connection, OptionalExtension, params};
use serde_json::{Value, json};
use std::path::Path;

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
        value["id"] = json!(id);
        value["title"] = row["title"].clone();
        value["url"] = row["url"].clone();
        let object = value.as_object_mut().unwrap();
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
            let value: Option<(String, String)> = self
                .db
                .query_row(
                    &format!("SELECT markdown,images FROM {table} WHERE problem_id=?"),
                    [&id],
                    |r| Ok((r.get(0)?, r.get(1)?)),
                )
                .optional()?;
            value.map(|(markdown,images)|Ok(json!({"markdown":markdown,"images":serde_json::from_str::<Value>(&images)?}))).transpose()
        };
        let base = read("solutions")?.ok_or_else(|| ApiError::missing("这道题还没有题解"))?;
        let detailed = read("detailed_solutions")?;
        Ok(json!({"id":id,"markdown":base["markdown"],"images":base["images"],"detailed":detailed}))
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
    pub fn asset(&self, sha256: &str) -> Result<Value, ApiError> {
        if sha256.len() != 64 || !sha256.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Err(ApiError::bad("资源摘要无效"));
        }
        let (mime, data): (String, Vec<u8>) = self.db.query_row(
            "SELECT mime,data FROM statement_assets WHERE sha256=?",
            [sha256],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
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
