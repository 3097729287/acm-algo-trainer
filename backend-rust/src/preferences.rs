use crate::{
    api::ApiError,
    catalogue::Catalogue,
    learning::{day, stamp},
    storage::PersonalStore,
};
use base64::{Engine, engine::general_purpose::STANDARD};
use chrono::{DateTime, Utc};
use rusqlite::{Connection, OptionalExtension};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const ALLOWED: &str = "panelStyle backdrop panelOpacity pageOpacities widgets theme accent motion compact collapsed favorites views readerWidth fontSize difficultyDisplay learnedLectures libraryPageSize navOrder navLabels navGroups hiddenNavPages onboardingUnlockedPages levelNoticeVersion levelNoticeSeen levelNoticePending seenAchievements showPlatforms onboardingCompleted onboardingGuideVersion avatarData navSchema learningPaths shortcuts editorTheme trainingListLocation";
const PAGES: &[&str] = &[
    "mine",
    "library",
    "training-lists",
    "competitions",
    "mock",
    "paths",
    "templates",
    "rankings",
    "growth",
    "records",
    "activity",
    "lectures",
    "settings",
    "wiki",
    "duel",
];
fn allowed(value: &Value, items: &[&str]) -> bool {
    value.as_str().is_some_and(|s| items.contains(&s))
}
fn integer(value: &Value, lo: i64, hi: i64) -> bool {
    value.as_i64().is_some_and(|v| lo <= v && v <= hi)
}
pub fn legacy_size(value: &Value) -> usize {
    match value {
        Value::Object(v) => {
            2 + v
                .iter()
                .map(|(k, v)| serde_json::to_string(k).unwrap().len() + 2 + legacy_size(v))
                .sum::<usize>()
                + v.len().saturating_sub(1) * 2
        }
        Value::Array(v) => {
            2 + v.iter().map(legacy_size).sum::<usize>() + v.len().saturating_sub(1) * 2
        }
        _ => value.to_string().len(),
    }
}
pub fn validate(value: &Value) -> Result<(), ApiError> {
    let object = value
        .as_object()
        .ok_or_else(|| ApiError::bad("偏好设置格式无效"))?;
    if object
        .keys()
        .any(|k| !ALLOWED.split_whitespace().any(|v| v == k))
    {
        return Err(ApiError::bad("偏好设置包含不支持的字段"));
    }
    for field in ["hiddenNavPages", "onboardingUnlockedPages"] {
        if let Some(v) = object.get(field) {
            if !v
                .as_array()
                .is_some_and(|a| a.len() <= PAGES.len() && a.iter().all(|v| allowed(v, PAGES)))
            {
                return Err(ApiError::bad("导航显示偏好无效"));
            }
        }
    }
    if value["hiddenNavPages"].as_array().is_some_and(|v| {
        v.iter()
            .any(|v| allowed(v, &["mine", "records", "settings"]))
    }) {
        return Err(ApiError::bad("我的训练和设置须保留"));
    }
    for (field, lo, hi, error) in [
        ("levelNoticeVersion", 0, 1, "等级提示版本无效"),
        ("levelNoticeSeen", 0, 100, "等级提示记录无效"),
        ("levelNoticePending", 0, 100, "等级提示记录无效"),
        ("navSchema", 1, 2, "导航版本无效"),
        ("onboardingGuideVersion", 0, 1000, "界面选项格式无效"),
        ("panelOpacity", 0, 100, "面板不透明度须为 0–100"),
        ("fontSize", 13, 22, "界面字号须为 13–22"),
        ("libraryPageSize", 10, 200, "题库每页题数须为 10–200"),
    ] {
        if object.get(field).is_some_and(|v| !integer(v, lo, hi)) {
            return Err(ApiError::bad(error));
        }
    }
    for field in ["widgets", "showPlatforms", "onboardingCompleted"] {
        if object.get(field).is_some_and(|v| !v.is_boolean()) {
            return Err(ApiError::bad(if field == "widgets" {
                "训练挂件选项无效"
            } else {
                "界面选项格式无效"
            }));
        }
    }
    for (field, options) in [
        ("difficultyDisplay", &["number", "text"][..]),
        (
            "panelStyle",
            &["minimal", "outlined", "aurora", "blueprint"][..],
        ),
        (
            "backdrop",
            &["none", "aurora", "grid", "sunset", "custom"][..],
        ),
        (
            "editorTheme",
            &[
                "auto",
                "rainbow-dark",
                "woodfish-dracula",
                "woodfish-black",
                "woodfish-neon",
                "woodfish-light",
                "one-dark",
                "dracula",
                "nord",
                "tokyo-night",
                "catppuccin",
                "github-dark",
                "monokai",
                "gruvbox",
                "solarized-dark",
                "ayu-dark",
                "rose-pine",
                "github-light",
                "one-light",
                "solarized-light",
                "ayu-light",
                "paper",
                "rose-pine-dawn",
            ][..],
        ),
    ] {
        if object.get(field).is_some_and(|v| !allowed(v, options)) {
            return Err(ApiError::bad(if field == "editorTheme" {
                "代码主题无效"
            } else {
                "外观选项无效"
            }));
        }
    }
    for field in ["favorites", "seenAchievements", "navOrder", "views"] {
        if object.get(field).is_some_and(|v| !v.is_array()) {
            return Err(ApiError::bad("偏好设置列表格式无效"));
        }
    }
    for field in ["navLabels", "navGroups"] {
        if object.get(field).is_some_and(|v| !v.is_object()) {
            return Err(ApiError::bad("导航偏好格式无效"));
        }
    }
    if object.get("learnedLectures").is_some_and(|v| {
        !v.as_array().is_some_and(|a| {
            a.len() <= 2048
                && a.iter().all(|v| {
                    v.as_str()
                        .is_some_and(|s| !s.is_empty() && s.chars().count() <= 240)
                })
        })
    }) {
        return Err(ApiError::bad("已学会的知识点格式无效"));
    }
    if object.get("seenAchievements").is_some_and(|v| {
        !v.as_array().is_some_and(|a| {
            a.len() <= 256
                && a.iter().all(|v| {
                    v.as_str().is_some_and(|s| {
                        !s.is_empty()
                            && s.len() <= 80
                            && s.bytes()
                                .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
                    })
                })
        })
    }) {
        return Err(ApiError::bad("成就已读记录格式无效"));
    }
    if object
        .get("learningPaths")
        .is_some_and(|v| !v.as_object().is_some_and(|o| o.len() <= 64))
    {
        return Err(ApiError::bad("题单进度格式无效"));
    }
    if let Some(shortcuts) = object.get("shortcuts") {
        let keys = "commands sidebar settings search refresh regions help practice solution favorite listSearch run submit official save pane-0 pane-1 pane-2 page-mine page-library page-training-lists page-templates page-paths page-competitions page-mock page-records page-growth page-activity page-lectures theme calendar daily-tasks achievements list-filter list-random list-difficulty list-recent workbench-back workbench-next statement-language statement-copy toolbar-lock initial-code code-templates workbench-solution console-toggle catalog-up catalog-home catalog-filter catalog-new contest-filter contest-folders contest-up mock-filter mock-regenerate lecture-learned lecture-fullscreen lecture-back template-copy template-back records-platform records-result ranking-daily ranking-weekly ranking-all initial-new initial-copy statement-font statement-original code-language workbench-undo learning-summary";
        if !shortcuts.as_object().is_some_and(|v| {
            v.iter().all(|(k, v)| {
                keys.split_whitespace().any(|s| s == k)
                    && v.as_str().is_some_and(|s| {
                        s.chars().count() <= 64 && !s.chars().any(|c| (c as u32) < 32)
                    })
            })
        }) {
            return Err(ApiError::bad("快捷键设置格式无效"));
        }
    }
    if let Some(opacities) = object.get("pageOpacities") {
        let keys = "mine library training-lists competitions mock rankings growth records activity lectures settings statement editor solution paths templates practice-toolbar practice-picker template-picker contest-statement contest-editor contest-toolbar contest-picker contest-calendar mock-statement mock-editor mock-toolbar mock-picker initial-code daily-tasks achievements level-up popups messages accounts wiki duel";
        if !opacities.as_object().is_some_and(|v| {
            v.iter()
                .all(|(k, v)| keys.split_whitespace().any(|s| s == k) && integer(v, 0, 100))
        }) {
            return Err(ApiError::bad("界面不透明度须为 0–100"));
        }
    }
    if let Some(location) = object.get("trainingListLocation") {
        if !location.as_object().is_some_and(|o| {
            o.keys()
                .all(|k| ["state", "scrollTop"].contains(&k.as_str()))
        }) || legacy_size(location) > 8192
            || location.get("state").is_some_and(|v| !v.is_object())
            || location
                .get("scrollTop")
                .is_some_and(|v| !v.as_f64().is_some_and(|n| (0.0..=1_000_000.).contains(&n)))
        {
            return Err(ApiError::bad("题单位置无效"));
        }
    }
    if let Some(avatar) = object.get("avatarData") {
        let value = avatar
            .as_str()
            .ok_or_else(|| ApiError::bad("头像图片格式无效"))?;
        if !value.is_empty() {
            let (kind, payload) = value
                .strip_prefix("data:image/")
                .and_then(|v| v.split_once(";base64,"))
                .ok_or_else(|| ApiError::bad("头像图片格式无效"))?;
            if !["png", "jpeg", "webp"].contains(&kind) || value.len() > 16_000_023 {
                return Err(ApiError::bad(
                    "头像须为不超过 12 MB 的 PNG、JPEG 或 WebP 图片",
                ));
            }
            let data = STANDARD
                .decode(payload)
                .map_err(|_| ApiError::bad("头像图片编码无效"))?;
            if data.len() > 12_000_000 {
                return Err(ApiError::bad(
                    "头像须为不超过 12 MB 的 PNG、JPEG 或 WebP 图片",
                ));
            }
            let valid = match kind {
                "png" => {
                    data.len() >= 24
                        && data.starts_with(b"\x89PNG\r\n\x1a\n")
                        && &data[12..16] == b"IHDR"
                }
                "jpeg" => {
                    data.len() >= 4
                        && data.starts_with(b"\xff\xd8\xff")
                        && data.ends_with(b"\xff\xd9")
                }
                "webp" => {
                    data.len() >= 16
                        && data.starts_with(b"RIFF")
                        && &data[8..12] == b"WEBP"
                        && u32::from_le_bytes(data[4..8].try_into().unwrap()) as usize
                            == data.len() - 8
                }
                _ => false,
            };
            if !valid {
                return Err(ApiError::bad("头像内容与图片类型不一致"));
            }
        }
    }
    let mut bounded = value.clone();
    bounded.as_object_mut().unwrap().remove("avatarData");
    if let Some(browser) = value.get("learningPaths").and_then(|v| v.get("browserV1")) {
        if !browser.is_null() {
            if !browser.is_object()
                || browser["version"] != 1
                || !browser["tabs"].as_array().is_some_and(|a| a.len() <= 64)
                || legacy_size(browser) > 24 * 1024 * 1024
            {
                return Err(ApiError::bad("学习标签页状态过大或格式无效"));
            }
            bounded["learningPaths"]
                .as_object_mut()
                .unwrap()
                .remove("browserV1");
        }
    }
    if legacy_size(&bounded) > 128 * 1024 {
        return Err(ApiError::bad("偏好设置过大，请减少收藏或保存的筛选"));
    }
    Ok(())
}
pub fn action(db: &Connection, kind: &str, key: &str, now: DateTime<Utc>) -> Result<(), ApiError> {
    let name = format!("activity-actions:{}", day(now));
    let previous: Option<String> = db
        .query_row(
            "SELECT value FROM account_preferences WHERE key=?",
            [&name],
            |r| r.get(0),
        )
        .optional()?;
    let mut events = previous
        .and_then(|v| serde_json::from_str::<Value>(&v).ok())
        .filter(Value::is_object)
        .unwrap_or(json!({}));
    let id = format!("{:x}", Sha256::digest(format!("{kind}\0{key}")));
    if events.get(&id).is_some() || events.as_object().unwrap().len() >= 512 {
        return Ok(());
    }
    events[&id] = json!({"kind":kind,"key":key,"at":stamp(now)});
    PersonalStore::put(db, &name, &events.to_string(), &stamp(now))
}
pub fn save(
    store: &mut PersonalStore,
    catalogue: Option<&Catalogue>,
    body: &Value,
    now: DateTime<Utc>,
) -> Result<Value, ApiError> {
    if body.as_object().map_or(0, |o| o.len()) != 1 || !body["preferences"].is_object() {
        return Err(ApiError::bad("偏好设置格式无效"));
    }
    let mut value = body["preferences"].clone();
    validate(&value)?;
    let previous = store.document("ui")?.unwrap_or(json!({}));
    if [
        "levelNoticeVersion",
        "levelNoticeSeen",
        "levelNoticePending",
    ]
    .iter()
    .any(|k| value.get(k).is_some() || previous.get(k).is_some())
    {
        let current = [&previous, &value]
            .into_iter()
            .filter(|v| v["levelNoticeVersion"] == 1)
            .collect::<Vec<_>>();
        let max = |key: &str| {
            current
                .iter()
                .filter_map(|v| v[key].as_i64().filter(|n| (0..=100).contains(n)))
                .max()
                .unwrap_or(0)
        };
        let seen = max("levelNoticeSeen");
        let pending = max("levelNoticePending");
        value["levelNoticeVersion"] = json!(if current.is_empty() { 0 } else { 1 });
        value["levelNoticeSeen"] = json!(seen);
        value["levelNoticePending"] = json!(if pending > seen { pending } else { 0 });
    }
    for field in ["onboardingUnlockedPages", "seenAchievements"] {
        if value.get(field).is_some() || previous.get(field).is_some() {
            let mut merged = Vec::new();
            for v in [&previous, &value] {
                for item in v[field].as_array().into_iter().flatten() {
                    if !merged.contains(item) {
                        merged.push(item.clone());
                    }
                }
            }
            if field == "onboardingUnlockedPages" {
                merged.retain(|v| allowed(v, PAGES));
                merged.sort_by(|a, b| a.as_str().cmp(&b.as_str()));
            }
            value[field] = json!(merged);
        }
    }
    if previous["onboardingCompleted"] == true {
        value["onboardingCompleted"] = true.into();
    }
    if previous.get("onboardingGuideVersion").is_some()
        || value.get("onboardingGuideVersion").is_some()
    {
        value["onboardingGuideVersion"] = json!(
            [&previous, &value]
                .iter()
                .filter_map(|v| v["onboardingGuideVersion"]
                    .as_i64()
                    .filter(|n| (0..=1000).contains(n)))
                .max()
                .unwrap_or(0)
        );
    }
    if previous != value || store.pref("ui")?.is_none() {
        let mut actions = Vec::new();
        if ["theme", "accent"].iter().any(|k| {
            previous
                .get(k)
                .unwrap_or(&json!(if *k == "theme" { "dark" } else { "violet" }))
                != value
                    .get(k)
                    .unwrap_or(&json!(if *k == "theme" { "dark" } else { "violet" }))
        }) {
            actions.push((
                "appearance",
                format!(
                    "{}/{}",
                    value["theme"].as_str().unwrap_or("dark"),
                    value["accent"].as_str().unwrap_or("violet")
                ),
            ));
        }
        for (field, kind) in [("favorites", "favorite"), ("learnedLectures", "learn")] {
            for id in value[field].as_array().into_iter().flatten() {
                if !previous[field].as_array().is_some_and(|a| a.contains(id)) {
                    let id = id
                        .as_str()
                        .ok_or_else(|| ApiError::bad("偏好设置列表格式无效"))?;
                    let key = if kind == "favorite" {
                        if let Some(catalogue) = catalogue {
                            if let Some(row) = catalogue.row(id, true)? {
                                row["url"]
                                    .as_str()
                                    .filter(|s| !s.is_empty())
                                    .unwrap_or(id)
                                    .to_owned()
                            } else {
                                continue;
                            }
                        } else {
                            id.into()
                        }
                    } else {
                        id.into()
                    };
                    actions.push((kind, key));
                }
            }
        }
        let tx = store.db.transaction()?;
        PersonalStore::put(&tx, "ui", &value.to_string(), &stamp(now))?;
        for (kind, key) in actions {
            action(&tx, kind, &key, now)?;
        }
        tx.commit()?;
    }
    store.preferences()
}
