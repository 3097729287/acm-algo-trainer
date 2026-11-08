use crate::{
    api::{ApiError, fields, now, required_text},
    storage::PersonalStore,
};
use serde_json::{Value, json};
use std::path::Path;

pub fn default_code(language: &str) -> Result<&'static str, ApiError> {
    match language {
        "cpp17" => Ok(
            "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    \n    return 0;\n}\n",
        ),
        "python3" => Ok(
            "import sys\n\ndef solve():\n    pass\n\nif __name__ == \"__main__\":\n    solve()\n",
        ),
        _ => Err(ApiError::bad("编程语言无效")),
    }
}
fn default_template(store: &PersonalStore, language: &str) -> Result<Value, ApiError> {
    let mut base = json!({"id":"default","title":"默认","language":language,"code":default_code(language)?,"builtin":true,"revision":""});
    if let Some(value) = store.document(&format!("initial-code-default:{language}"))? {
        let fields = value.as_object().ok_or_else(|| {
            ApiError::new(500, "INVALID_STORED_DATA", "模板记录格式异常，原数据已保留")
        })?;
        if value["deleted"] != true {
            if fields.get("id").is_some_and(|v| v != "default")
                || fields.get("language").is_some_and(|v| v != language)
                || fields.get("code").is_some_and(|v| {
                    !v.as_str()
                        .is_some_and(|s| s.len() <= 65536 && !s.contains('\0'))
                })
                || fields.get("revision").is_some_and(|v| !v.is_string())
            {
                return Err(ApiError::new(
                    500,
                    "INVALID_STORED_DATA",
                    "模板记录格式异常，原数据已保留",
                ));
            }
            base.as_object_mut().unwrap().extend(fields.clone());
            base["customized"] = json!(true);
        }
    }
    Ok(base)
}
fn valid_id(value: &str, prefix: &str) -> bool {
    value.strip_prefix(prefix).is_some_and(|s| {
        s.len() == 32
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
fn owned(store: &PersonalStore, prefix: &str) -> Result<Vec<Value>, ApiError> {
    let documents = store.documents(prefix)?;
    if documents.iter().any(|v| !v.is_object()) {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "模板记录格式异常，原数据已保留",
        ));
    }
    let mut values = documents
        .into_iter()
        .filter(|v| v.get("deleted") != Some(&json!(true)))
        .collect::<Vec<_>>();
    values.sort_by_key(|v| {
        (
            v["title"].as_str().unwrap_or("").to_lowercase(),
            v["id"].as_str().unwrap_or("").to_owned(),
        )
    });
    Ok(values)
}
pub fn initial_selected(store: &PersonalStore) -> Result<Value, ApiError> {
    let mut selection = json!({});
    let mut revisions = json!({});
    let mut templates = Vec::new();
    for language in ["cpp17", "python3"] {
        let choice = store
            .document(&format!("initial-code-selection:{language}"))?
            .unwrap_or(json!({}));
        let id = choice["id"].as_str().unwrap_or("default");
        let value = if valid_id(id, "initial-code:") {
            store.document(id)?
        } else {
            None
        };
        let value = match value.filter(|v| v["language"] == language && v["deleted"] != true) {
            Some(value) => value,
            None => default_template(store, language)?,
        };
        selection[language] = value["id"].clone();
        revisions[language] = choice.get("revision").cloned().unwrap_or(json!(""));
        templates.push(value);
    }
    Ok(json!({"selection":selection,"revisions":revisions,"templates":templates}))
}
pub fn initial_catalog(store: &PersonalStore) -> Result<Value, ApiError> {
    let mut value = initial_selected(store)?;
    let mut templates = vec![
        default_template(store, "cpp17")?,
        default_template(store, "python3")?,
    ];
    templates.extend(owned(store, "initial-code:")?);
    value["templates"] = json!(templates);
    Ok(value)
}
pub fn initial_choose(store: &PersonalStore, body: &Value) -> Result<Value, ApiError> {
    fields(body, &["id", "language", "revision"])?;
    if body.as_object().map_or(0, |o| o.len()) != 3 {
        return Err(ApiError::bad("初始代码模板选择无效"));
    }
    let language = required_text(body, "language", 16)?;
    default_code(language)?;
    let id = required_text(body, "id", 100)?;
    if id != "default" {
        if !valid_id(id, "initial-code:") {
            return Err(ApiError::bad("初始代码模板无效"));
        }
        let value = store
            .document(id)?
            .ok_or_else(|| ApiError::missing("没有找到这个初始代码模板"))?;
        if value["deleted"] == true || value["language"] != language {
            return Err(ApiError::missing("没有找到这个初始代码模板"));
        }
    }
    let key = format!("initial-code-selection:{language}");
    let previous = store.document(&key)?.unwrap_or(json!({}));
    if body["revision"] != previous.get("revision").cloned().unwrap_or(json!("")) {
        return Err(ApiError::conflict(
            "初始代码模板已在其它位置修改，请重新读取后选择",
        ));
    }
    if previous
        .get("id")
        .and_then(Value::as_str)
        .unwrap_or("default")
        != id
    {
        store.put_document(
            &key,
            &json!({"id":id,"revision":uuid::Uuid::new_v4().simple().to_string()}),
        )?;
    }
    initial_catalog(store)
}
pub fn initial_save(store: &mut PersonalStore, body: &Value) -> Result<Value, ApiError> {
    fields(
        body,
        &["id", "title", "language", "code", "revision", "delete"],
    )?;
    let id = body.get("id").and_then(Value::as_str);
    if body
        .get("id")
        .is_some_and(|v| !v.is_null() && !v.is_string())
        || id.is_some_and(|id| id != "default" && !valid_id(id, "initial-code:"))
    {
        return Err(ApiError::bad("默认模板请另存为自己的模板"));
    }
    if body.get("delete").is_some_and(|v| !v.is_boolean()) {
        return Err(ApiError::bad("初始代码模板操作无效"));
    }
    if id == Some("default") {
        let language = required_text(body, "language", 16)?;
        default_code(language)?;
        if body["delete"] == true || body["title"] != "默认" {
            return Err(ApiError::bad("默认模板不能删除或重命名"));
        }
        let mut value = default_template(store, language)?;
        if body.get("revision").cloned().unwrap_or(json!("")) != value["revision"] {
            return Err(ApiError::conflict(
                "初始代码模板已在其它位置修改，请重新读取后保存",
            ));
        }
        let code = body["code"]
            .as_str()
            .filter(|s| s.len() <= 65536 && !s.contains('\0'))
            .ok_or_else(|| ApiError::bad("代码不得超过 64 KiB"))?;
        let stamp = now();
        value["code"] = json!(code);
        value["customized"] = json!(true);
        value["revision"] = json!(uuid::Uuid::new_v4().simple().to_string());
        value["updatedAt"] = json!(stamp);
        let tx = store.db.transaction()?;
        PersonalStore::put(
            &tx,
            &format!("initial-code-default:{language}"),
            &value.to_string(),
            &stamp,
        )?;
        tx.commit()?;
        let mut result = initial_catalog(store)?;
        result["template"] = value;
        return Ok(result);
    }
    let previous = id.map(|id| store.document(id)).transpose()?.flatten();
    if previous.as_ref().is_some_and(|v| !v.is_object()) {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "模板记录格式异常，原数据已保留",
        ));
    }
    if id.is_some() && previous.as_ref().is_none_or(|v| v["deleted"] == true) {
        return Err(ApiError::missing("没有找到这个初始代码模板"));
    }
    if previous
        .as_ref()
        .is_some_and(|v| v["revision"] != body["revision"])
    {
        return Err(ApiError::conflict(
            "初始代码模板已在其它位置修改，请重新读取后保存",
        ));
    }
    let stamp = now();
    let revision = uuid::Uuid::new_v4().simple().to_string();
    let value = if body["delete"] == true {
        let mut v = previous
            .clone()
            .ok_or_else(|| ApiError::missing("没有找到这个初始代码模板"))?;
        v["deleted"] = true.into();
        v["revision"] = json!(revision);
        v["updatedAt"] = json!(stamp);
        v
    } else {
        let title = required_text(body, "title", 120)?.trim();
        let language = required_text(body, "language", 16)?;
        default_code(language)?;
        let code = body
            .get("code")
            .and_then(Value::as_str)
            .filter(|v| v.len() <= 65536 && !v.contains('\0'))
            .ok_or_else(|| ApiError::bad("代码不得超过 64 KiB"))?;
        if title.is_empty() || title.chars().any(char::is_control) {
            return Err(ApiError::bad("请填写模板名称"));
        }
        if previous.as_ref().is_some_and(|v| v["language"] != language) {
            return Err(ApiError::bad("请为其它语言另建模板"));
        }
        if previous.is_none() && owned(store, "initial-code:")?.len() >= 32 {
            return Err(ApiError::bad("初始代码模板已达 32 个，请先整理已有模板"));
        }
        json!({"id":id.map(String::from).unwrap_or_else(||format!("initial-code:{}",uuid::Uuid::new_v4().simple())),"title":title,"language":language,"code":code,"builtin":false,
            "revision":revision,"createdAt":previous.as_ref().and_then(|v|v.get("createdAt")).cloned().unwrap_or(json!(stamp)),"updatedAt":stamp})
    };
    let tx = store.db.transaction()?;
    PersonalStore::put(
        &tx,
        value["id"].as_str().unwrap(),
        &value.to_string(),
        &stamp,
    )?;
    if value["deleted"] == true {
        let key = format!(
            "initial-code-selection:{}",
            value["language"].as_str().unwrap()
        );
        let current = tx.query_row(
            "SELECT value FROM account_preferences WHERE key=?",
            [&key],
            |r| r.get::<_, String>(0),
        );
        match current {
            Ok(v) => {
                let current: Value = serde_json::from_str(&v)?;
                if current["id"] == value["id"] {
                    PersonalStore::put(&tx,&key,&json!({"id":"default","revision":uuid::Uuid::new_v4().simple().to_string()}).to_string(),&stamp)?;
                }
            }
            Err(rusqlite::Error::QueryReturnedNoRows) => {}
            Err(e) => return Err(e.into()),
        }
    }
    tx.commit()?;
    let mut catalog = initial_catalog(store)?;
    catalog["template"] = value;
    Ok(catalog)
}

pub fn builtin_templates(resources: &Path) -> Result<Vec<Value>, ApiError> {
    let base: Value =
        serde_json::from_slice(&std::fs::read(resources.join("code-templates.json"))?)?;
    let teaching: Value =
        serde_json::from_slice(&std::fs::read(resources.join("template-teaching.json"))?)?;
    let mut result = Vec::new();
    for source in [base.get("templates"), teaching.get("templates")] {
        for item in source.and_then(Value::as_array).into_iter().flatten() {
            let mut value = item.clone();
            let id = item["id"]
                .as_str()
                .unwrap_or("")
                .trim_start_matches("builtin:");
            if let Some(lesson) = teaching.get("topics").and_then(|v| v.get(id)) {
                value["curriculum"] = lesson.clone();
                if value.get("learningPath").is_none() {
                    value["learningPath"] = lesson["learningPath"].clone();
                }
                value["explanation"] = json!(
                    [
                        item["explanation"].as_str().unwrap_or(""),
                        lesson["markdown"].as_str().unwrap_or("")
                    ]
                    .into_iter()
                    .filter(|s| !s.is_empty())
                    .collect::<Vec<_>>()
                    .join("\n\n")
                );
            }
            result.push(value);
        }
    }
    Ok(result)
}
pub fn catalog(store: &PersonalStore, builtins: &[Value]) -> Result<Value, ApiError> {
    let mut st=store.db.prepare("SELECT DISTINCT problem_id FROM submissions WHERE scope='template' AND verdict='AC' AND mode='submit' AND finished_at IS NOT NULL")?;
    let passed = st
        .query_map([], |r| r.get::<_, String>(0))?
        .collect::<Result<std::collections::HashSet<_>, _>>()?;
    let mut templates = Vec::new();
    for item in builtins {
        let mut value = item.clone();
        value["practicePassed"] = json!(
            item["practiceIds"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|v| v.as_str().is_some_and(|v| passed.contains(v)))
                .collect::<Vec<_>>()
        );
        templates.push(value);
    }
    templates.extend(owned(store, "custom-template:")?);
    Ok(json!({"templates":templates}))
}
pub fn save(store: &PersonalStore, body: &Value, builtins: &[Value]) -> Result<Value, ApiError> {
    fields(
        body,
        &[
            "id", "title", "category", "language", "code", "notes", "summary", "revision", "delete",
        ],
    )?;
    let id = body.get("id").and_then(Value::as_str);
    if body
        .get("id")
        .is_some_and(|v| !v.is_null() && !v.is_string())
        || id.is_some_and(|id| !valid_id(id, "custom-template:"))
    {
        return Err(ApiError::bad("内置模板请另存为自己的模板"));
    }
    if body.get("delete").is_some_and(|v| !v.is_boolean()) {
        return Err(ApiError::bad("模板操作无效"));
    }
    let previous = id.map(|id| store.document(id)).transpose()?.flatten();
    if previous.as_ref().is_some_and(|v| !v.is_object()) {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "模板记录格式异常，原数据已保留",
        ));
    }
    if id.is_some() && previous.as_ref().is_none_or(|v| v["deleted"] == true) {
        return Err(ApiError::missing("没有找到这个模板"));
    }
    if previous
        .as_ref()
        .is_some_and(|v| v["revision"] != body["revision"])
    {
        return Err(ApiError::conflict("模板已在其它位置修改，请重新读取后保存"));
    }
    let stamp = now();
    let revision = uuid::Uuid::new_v4().simple().to_string();
    let value = if body["delete"] == true {
        let mut value = previous
            .clone()
            .ok_or_else(|| ApiError::missing("没有找到这个模板"))?;
        value["deleted"] = true.into();
        value["revision"] = json!(revision);
        value["updatedAt"] = json!(stamp);
        value
    } else {
        let mut fields = json!({});
        for (key, maximum) in [
            ("title", 120),
            ("category", 40),
            ("language", 16),
            ("code", 65536),
            ("notes", 16384),
            ("summary", 400),
        ] {
            let value = match body.get(key) {
                None => "",
                Some(v) => v
                    .as_str()
                    .ok_or_else(|| ApiError::bad("模板内容格式无效"))?,
            };
            if value.len() > maximum || value.contains('\0') {
                return Err(ApiError::bad("模板内容过长或格式无效"));
            }
            fields[key] = json!(value);
        }
        let title = fields["title"].as_str().unwrap().trim().to_owned();
        let category = fields["category"].as_str().unwrap().trim().to_owned();
        if title.is_empty() || fields["code"].as_str().unwrap().trim().is_empty() {
            return Err(ApiError::bad("请填写模板名称、语言和代码"));
        }
        default_code(fields["language"].as_str().unwrap())?;
        if previous.is_none() && owned(store, "custom-template:")?.len() >= 128 {
            return Err(ApiError::bad("自建模板已达 128 个，请先整理已有模板"));
        }
        fields["title"] = json!(title);
        fields["category"] = json!(if category.is_empty() {
            "我的模板".to_owned()
        } else {
            category
        });
        fields["id"] = json!(
            id.map(String::from)
                .unwrap_or_else(|| format!("custom-template:{}", uuid::Uuid::new_v4().simple()))
        );
        fields["builtin"] = false.into();
        fields["tags"] = json!([]);
        fields["revision"] = json!(revision);
        fields["createdAt"] = previous
            .as_ref()
            .and_then(|v| v.get("createdAt"))
            .cloned()
            .unwrap_or(json!(stamp));
        fields["updatedAt"] = json!(stamp);
        fields
    };
    store.put_document(value["id"].as_str().unwrap(), &value)?;
    let mut templates = builtins.to_vec();
    templates.extend(owned(store, "custom-template:")?);
    Ok(json!({"template":value,"templates":templates}))
}
