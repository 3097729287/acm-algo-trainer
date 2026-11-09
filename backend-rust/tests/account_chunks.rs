use chrono::{TimeZone, Utc};
use flate2::{Compression, GzBuilder};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::io::Write;
use std::process::Command;
use tobe_core::ApiError;
use tobe_core::account_chunks::{self as chunks, CODE_PREFIX, ChunkObject, ObjectKind, TABLES};

type Graph = BTreeMap<String, ChunkObject>;
fn store(graph: &mut Graph, object: &ChunkObject) -> Result<(), ApiError> {
    graph.insert(object.hash.clone(), object.clone());
    Ok(())
}
fn load(graph: &Graph, key: &str) -> Result<ChunkObject, ApiError> {
    graph.get(key).cloned().ok_or_else(|| {
        ApiError::new(
            503,
            "SYNTHETIC_CACHE_MISS",
            "not available in this isolated owner cache",
        )
    })
}
fn put(graph: &mut Graph, raw: &[u8]) -> String {
    chunks::write_blob(raw, &[], &mut |object| store(graph, object)).unwrap()
}
fn digest(raw: &[u8]) -> String {
    format!("{:x}", Sha256::digest(raw))
}
fn gzip(raw: &[u8]) -> Vec<u8> {
    let mut output = GzBuilder::new()
        .mtime(0)
        .operating_system(3)
        .write(Vec::new(), Compression::new(6));
    output.write_all(raw).unwrap();
    output.finish().unwrap()
}
fn object(kind: ObjectKind, payload: Vec<u8>, mut children: Vec<String>) -> ChunkObject {
    children.sort();
    children.dedup();
    let mut hasher = Sha256::new();
    hasher.update(kind.as_str());
    hasher.update(b"\n");
    for child in &children {
        hasher.update(child);
    }
    hasher.update(b"\n");
    hasher.update(&payload);
    ChunkObject {
        hash: format!("{:x}", hasher.finalize()),
        kind,
        payload,
        children,
    }
}
fn insert(graph: &mut Graph, value: ChunkObject) -> String {
    let key = value.hash.clone();
    graph.insert(key.clone(), value);
    key
}
fn index(graph: &mut Graph, parts: &[String], children: &[String]) -> String {
    insert(
        graph,
        object(
            ObjectKind::Concat,
            gzip(&chunks::encode(&json!({"parts":parts})).unwrap()),
            children.to_vec(),
        ),
    )
}
fn empty() -> Value {
    json!({"format":"tb-account-state-v1", "tables":{}, "publicAccounts":{}})
}
fn reference(root: &str, bytes: &[u8], offset: usize) -> String {
    format!(
        "{CODE_PREFIX}{}",
        String::from_utf8(
            chunks::encode(
                &json!({"root":root,"sha256":digest(bytes),"bytes":bytes.len(),"offset":offset})
            )
            .unwrap()
        )
        .unwrap()
    )
}
fn fail(error: ApiError) {
    assert!(
        matches!(
            error.code.as_str(),
            "ACCOUNT_CHUNK_INVALID" | "ACCOUNT_CHUNK_LIMIT"
        ),
        "{error:?}"
    );
    assert!(
        !error.retryable && !error.uncertain,
        "data errors must not grant an offline lease"
    );
}

#[test]
fn python_oracle_reads_rust_and_rust_reads_actual_python_objects() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("python.json");
    let helper = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/support/account_chunks_oracle.py");
    let python = std::env::var("TB_NATIVE_TEST_PYTHON")
        .expect("set TB_NATIVE_TEST_PYTHON for the test-only old Python oracle");
    let output = Command::new(&python)
        .arg(&helper)
        .arg("export")
        .arg(&path)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let value: Value = serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    let mut graph = Graph::new();
    for item in value["objects"].as_array().unwrap() {
        let object = chunks::from_wire(item["hash"].as_str().unwrap(), item).unwrap();
        assert_eq!(chunks::to_wire(&object).unwrap(), *item);
        store(&mut graph, &object).unwrap();
    }
    let unpacked = chunks::unpack_state(value["root"].as_str().unwrap(), &mut |key| {
        load(&graph, key)
    })
    .unwrap();
    assert!(!unpacked.duplicate_learning_summary);
    let mut expected = value["canonical"].clone();
    for &(table, keys) in TABLES {
        expected["tables"][table]
            .as_array_mut()
            .unwrap()
            .sort_by_key(|row| {
                keys.iter()
                    .map(|key| {
                        if let Some(text) = row[*key].as_str() {
                            text.to_owned()
                        } else {
                            row[*key].to_string()
                        }
                    })
                    .collect::<Vec<_>>()
            });
    }
    assert_eq!(unpacked.state, expected);
    let legacy = chunks::code_reference(value["legacyReference"].as_str().unwrap())
        .unwrap()
        .unwrap();
    assert_eq!(legacy.offset(), 0);
    assert_eq!(
        chunks::read_code(&legacy, &mut |key| load(&graph, key)).unwrap(),
        value["legacyCode"]
    );
    let before = value["state"].clone();
    let mut rust_graph = Graph::new();
    let canonical = chunks::canonicalize_state(
        &before,
        &BTreeMap::new(),
        Utc.with_ymd_and_hms(2026, 11, 9, 12, 0, 0).unwrap(),
        &mut |object| store(&mut rust_graph, object),
    )
    .unwrap();
    assert_eq!(before, value["state"]);
    let original = before["tables"]["submissions"].as_array().unwrap();
    let python_rows = value["canonical"]["tables"]["submissions"]
        .as_array()
        .unwrap();
    let mut codes = Vec::new();
    for (index, row) in canonical.state["tables"]["submissions"]
        .as_array()
        .unwrap()
        .iter()
        .enumerate()
    {
        let actual = chunks::code_reference(row["code"].as_str().unwrap()).unwrap();
        let oracle = chunks::code_reference(python_rows[index]["code"].as_str().unwrap()).unwrap();
        match (actual, oracle) {
            (Some(actual), Some(oracle)) => {
                assert_eq!(
                    (actual.sha256(), actual.bytes(), actual.offset()),
                    (oracle.sha256(), oracle.bytes(), oracle.offset())
                );
                assert_eq!(
                    chunks::read_code(&actual, &mut |key| load(&rust_graph, key)).unwrap(),
                    original[index]["code"]
                );
                codes.push(
                    json!({"id":row["id"],"reference":row["code"],"code":original[index]["code"]}),
                );
            }
            (None, None) => assert_eq!(row, &python_rows[index]),
            _ => panic!("different 30-day archive decision"),
        }
    }
    assert_eq!(codes.len(), canonical.code_references.len());
    let root = chunks::pack_state(&canonical.state, &mut |object| {
        store(&mut rust_graph, object)
    })
    .unwrap();
    let rust_unpacked = chunks::unpack_state(&root, &mut |key| load(&rust_graph, key)).unwrap();
    let rust_wire: Vec<_> = rust_graph
        .values()
        .map(|object| chunks::to_wire(object).unwrap())
        .collect();
    let rust_path = directory.path().join("rust.json");
    std::fs::write(
        &rust_path,
        chunks::encode(
            &json!({"root":root,"objects":rust_wire,"unpacked":rust_unpacked.state,"codes":codes}),
        )
        .unwrap(),
    )
    .unwrap();
    let output = Command::new(&python)
        .arg(&helper)
        .arg("verify")
        .arg(&rust_path)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let receipt: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(receipt["pythonReadRustManifest"], true);
    assert_eq!(receipt["pythonReadRustCodes"], codes.len());
    assert_eq!(receipt["httpRequests"], 0);
    assert_eq!(receipt["graphCallbacksHeldLock"], false);
    // Compare f64 values by bit pattern, not through the JSON parser's float algorithm.
    for vector in value["floatVectors"].as_array().unwrap() {
        let bits = vector["bits"].as_str().unwrap().parse::<u64>().unwrap();
        let actual =
            String::from_utf8(chunks::encode(&json!(f64::from_bits(bits))).unwrap()).unwrap();
        assert_eq!(
            actual,
            vector["json"].as_str().unwrap(),
            "float bits={bits}"
        );
        let parsed: Value = serde_json::from_str(vector["json"].as_str().unwrap()).unwrap();
        assert_eq!(
            parsed.as_f64().unwrap().to_bits(),
            bits,
            "decode float bits={bits}"
        );
        assert_eq!(
            String::from_utf8(chunks::encode(&parsed).unwrap()).unwrap(),
            vector["json"].as_str().unwrap()
        );
    }
    if let Some(path) = std::env::var_os("TB_ACCOUNT_CHUNKS_PROOF") {
        let proof = json!({"fixture":"synthetic, generated by actual Python protocol methods",
            "pythonSources":value["sources"],"pythonGraphObjects":graph.len(),"rustGraphObjects":rust_graph.len(),
            "pythonRootRetained":value["root"],"rustNewRoot":root,"gzipBytesDiffer":root!=value["root"].as_str().unwrap(),
            "tables":TABLES.len(),"pythonFloatVectors":value["floatVectors"].as_array().unwrap().len(),
            "pythonReadRustManifest":true,"rustReadPythonManifest":true,"twoWayCodeFiles":codes.len(),
            "localOriginalCodeRetained":before==value["state"],"httpRequests":0,"graphCallbacksHeldLock":false});
        std::fs::write(path, serde_json::to_vec_pretty(&proof).unwrap()).unwrap();
    }
}

#[test]
fn canonical_json_preserves_unicode_controls_integers_and_floats() {
    let value = json!({"中":"\u{2028}😀\u{0}\u{7}\n\r\t\u{8}\u{c}","a":[-0.0,1e-5,1e-4,1e15,1e16,i64::MIN,u64::MAX,true,null]});
    assert_eq!(
        String::from_utf8(chunks::encode(&value).unwrap()).unwrap(),
        "{\"a\":[-0.0,1e-05,0.0001,1000000000000000.0,1e+16,-9223372036854775808,18446744073709551615,true,null],\"中\":\" 😀\\u0000\\u0007\\n\\r\\t\\b\\f\"}"
    );
}

#[test]
fn real_python_float_roundtrip_counterexample_retains_the_original_value() {
    let expected = f64::from_bits(5_057_307_314_743_624_973);
    let encoded = chunks::encode(&json!(expected)).unwrap();
    let parsed: Value = serde_json::from_slice(&encoded).unwrap();
    assert_eq!(parsed.as_f64().unwrap().to_bits(), expected.to_bits());
    assert_eq!(chunks::encode(&parsed).unwrap(), encoded);
}

#[test]
fn wire_accepts_only_precise_get_or_upload_fields_and_rechecks_cache_objects() {
    let mut graph = Graph::new();
    let root = put(&mut graph, b"bytes");
    let item = graph[&root].clone();
    let wire = chunks::to_wire(&item).unwrap();
    let mut get = wire.clone();
    get.as_object_mut().unwrap().remove("hash");
    assert_eq!(chunks::from_wire(&root, &get).unwrap(), item);
    for (key, replacement) in [
        ("kind", json!("bad")),
        ("data", json!("!")),
        ("data", json!(0)),
        ("children", json!([null])),
        ("hash", json!("f".repeat(64))),
    ] {
        let mut changed = wire.clone();
        changed[key] = replacement;
        fail(chunks::from_wire(&root, &changed).unwrap_err());
    }
    let mut changed = wire.clone();
    changed["extra"] = json!(true);
    fail(chunks::from_wire(&root, &changed).unwrap_err());
    for children in [
        vec!["a".repeat(64), "a".repeat(64)],
        vec!["b".repeat(64), "a".repeat(64)],
        vec!["A".repeat(64)],
    ] {
        let mut changed = wire.clone();
        changed["children"] = json!(children);
        fail(chunks::from_wire(&root, &changed).unwrap_err());
    }
    let mut bad = item.clone();
    bad.payload[0] ^= 1;
    fail(chunks::read_blob(&root, chunks::RAW_LIMIT, &mut |_| Ok(bad.clone())).unwrap_err());
    fail(chunks::from_wire("bad", &wire).unwrap_err());
    let mut bad = wire;
    bad["data"] = json!("A".repeat(chunks::PAYLOAD_LIMIT.div_ceil(3) * 4 + 4));
    fail(chunks::from_wire(&root, &bad).unwrap_err());
}

#[test]
fn gzip_members_padding_crc_truncation_and_expansion_are_bounded() {
    let mut payload = gzip(b"one");
    payload.extend(gzip(b"two"));
    payload.extend([0, 0, 0]);
    let item = object(ObjectKind::Data, payload, vec![]);
    assert_eq!(
        chunks::read_blob(&item.hash, 6, &mut |_| Ok(item.clone())).unwrap(),
        b"onetwo"
    );
    let mut bad_crc = gzip(b"crc");
    let index = bad_crc.len() - 8;
    bad_crc[index] ^= 1;
    for payload in [
        Vec::new(),
        vec![0; 12],
        b"plain".to_vec(),
        bad_crc,
        gzip(b"short")[..12].to_vec(),
        [gzip(b"a"), b"garbage".to_vec()].concat(),
        gzip(&vec![b'x'; chunks::CHUNK + 1]),
    ] {
        let item = object(ObjectKind::Data, payload, vec![]);
        fail(
            chunks::read_blob(&item.hash, chunks::RAW_LIMIT, &mut |_| Ok(item.clone()))
                .unwrap_err(),
        );
    }
}

#[test]
fn blobs_keep_shared_parts_order_and_do_not_fetch_unrelated_cold_dependencies() {
    let mut graph = Graph::new();
    let data = vec![b'a'; chunks::CHUNK * 129 + 17];
    let cold = (0..300)
        .map(|i| digest(format!("cold-{i}").as_bytes()))
        .collect::<Vec<_>>();
    let root = chunks::write_blob(&data, &cold, &mut |item| store(&mut graph, item)).unwrap();
    assert_eq!(
        chunks::read_blob(&root, data.len(), &mut |key| load(&graph, key)).unwrap(),
        data
    );
    assert!(
        graph.len() < 20,
        "identical data chunks share content identities"
    );
    for item in graph.values() {
        assert!(item.children.len() <= 256);
    }
    let empty = put(&mut graph, b"");
    assert!(
        chunks::read_blob(&empty, 0, &mut |key| load(&graph, key))
            .unwrap()
            .is_empty()
    );
    fail(chunks::read_blob(&root, 5, &mut |key| load(&graph, key)).unwrap_err());
}

#[test]
fn graph_depth_parts_membership_and_output_limits_reject_before_returning_data() {
    let mut graph = Graph::new();
    let leaf = insert(&mut graph, object(ObjectKind::Data, gzip(b"x"), vec![]));
    let mut root = leaf.clone();
    for _ in 0..24 {
        root = index(&mut graph, &[root.clone()], &[root]);
    }
    assert_eq!(
        chunks::read_blob(&root, 1, &mut |key| load(&graph, key)).unwrap(),
        b"x"
    );
    root = index(&mut graph, &[root.clone()], &[root]);
    fail(chunks::read_blob(&root, 1, &mut |key| load(&graph, key)).unwrap_err());
    let bad = index(&mut graph, &vec![leaf.clone(); 129], &[leaf.clone()]);
    fail(chunks::read_blob(&bad, 1000, &mut |key| load(&graph, key)).unwrap_err());
    let bad = index(&mut graph, &[leaf], &[]);
    fail(chunks::read_blob(&bad, 1000, &mut |key| load(&graph, key)).unwrap_err());
    fail(
        chunks::read_blob(&bad, chunks::RAW_LIMIT + 1, &mut |_| {
            panic!("invalid maximum must fail before load")
        })
        .unwrap_err(),
    );
}

#[test]
fn all_seventeen_tables_round_trip_missing_tables_become_empty_and_keys_are_strict() {
    let mut state = empty();
    for &(table, keys) in TABLES {
        let mut row = json!({"data":"kept","extra":{"unicode":"中文😀"}});
        for key in keys {
            row[*key] = json!(format!("{table}:{key}"));
        }
        if ["tb_rank_profile", "official_xp_state"].contains(&table) {
            row["id"] = json!(1);
        }
        state["tables"][table] = json!([row]);
    }
    let mut graph = Graph::new();
    let root = chunks::pack_state(&state, &mut |item| store(&mut graph, item)).unwrap();
    assert_eq!(
        chunks::unpack_state(&root, &mut |key| load(&graph, key))
            .unwrap()
            .state,
        state
    );
    let root = chunks::pack_state(&empty(), &mut |item| store(&mut graph, item)).unwrap();
    let restored = chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap();
    assert_eq!(restored.state["tables"].as_object().unwrap().len(), 17);
    for bad in [
        json!([{"id":true}]),
        json!([{"id":1.0}]),
        json!([{"id":null}]),
        json!([{}]),
        json!([{"id":1},{"id":1}]),
    ] {
        let mut changed = empty();
        changed["tables"]["tb_rank_profile"] = bad;
        fail(chunks::pack_state(&changed, &mut |item| store(&mut graph, item)).unwrap_err());
    }
    let mut changed = empty();
    changed["tables"]["training"] = json!([{"id":1}]);
    fail(chunks::pack_state(&changed, &mut |item| store(&mut graph, item)).unwrap_err());
    changed["tables"]["training"] = json!([{"id":"x"},{"id":"x"}]);
    fail(chunks::pack_state(&changed, &mut |item| store(&mut graph, item)).unwrap_err());
    let mut changed = empty();
    changed["tables"]["unknown"] = json!([]);
    fail(chunks::pack_state(&changed, &mut |item| store(&mut graph, item)).unwrap_err());
}

fn manifest_for(graph: &mut Graph, table: &str, groups: &[Value]) -> String {
    let mut tables = serde_json::Map::new();
    for &(name, _) in TABLES {
        tables.insert(name.to_owned(), json!([]));
    }
    let entries:Vec<_>=groups.iter().enumerate().map(|(i,rows)| json!({"bucket":format!("{i}"),"root":put(graph,&chunks::encode(rows).unwrap())})).collect();
    tables.insert(table.to_owned(), json!(entries));
    let profile = put(graph, b"{}");
    put(
        graph,
        &chunks::encode(
            &json!({"format":"tb-private-chunk-state-v2","tables":tables,"publicAccounts":profile}),
        )
        .unwrap(),
    )
}

#[test]
fn legacy_summary_duplicates_are_preserved_and_flagged_while_other_duplicates_fail() {
    let mut graph = Graph::new();
    let rows = json!([{"key":"learning-summary-v1","value":"old-a"},{"key":"learning-summary-v1","value":"old-b"}]);
    let root = manifest_for(&mut graph, "account_preferences", &[rows.clone()]);
    let state = chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap();
    assert!(state.duplicate_learning_summary);
    assert_eq!(state.state["tables"]["account_preferences"], rows);
    for groups in [
        vec![json!([{"id":"same"},{"id":"same"}])],
        vec![json!([{"id":"same"}]), json!([{"id":"same"}])],
        vec![json!([{"id":null}])],
        vec![json!([{}])],
        vec![json!([3])],
    ] {
        let root = manifest_for(&mut graph, "training", &groups);
        fail(chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap_err());
    }
}

#[test]
fn code_references_require_exact_types_ranges_hashes_and_utf8() {
    let mut graph = Graph::new();
    let raw = "prefix中文😀tail".as_bytes();
    let root = put(&mut graph, raw);
    let serialized = reference(&root, "中文😀".as_bytes(), 6);
    let value = chunks::code_reference(&serialized).unwrap().unwrap();
    assert_eq!(
        chunks::read_code(&value, &mut |key| load(&graph, key)).unwrap(),
        "中文😀"
    );
    assert_eq!(
        chunks::code_reference("ordinary local source").unwrap(),
        None
    );
    for raw in [
        json!({"root":root,"sha256":digest(b"x"),"bytes":true}),
        json!({"root":root,"sha256":digest(b"x"),"bytes":1.0}),
        json!({"root":root,"sha256":digest(b"x"),"bytes":1,"offset":-1}),
        json!({"root":root,"sha256":digest(b"x"),"bytes":262144,"offset":1}),
        json!({"root":root,"sha256":"A".repeat(64),"bytes":1}),
        json!({"root":root,"sha256":digest(b"x"),"bytes":1,"extra":0}),
        json!([]),
    ] {
        fail(chunks::code_reference(&format!("{CODE_PREFIX}{raw}")).unwrap_err());
    }
    for (raw, offset, bytes) in [
        (vec![0xff], 0, vec![0xff]),
        (b"abc".to_vec(), 0, b"wrong".to_vec()),
        (b"abc".to_vec(), 100, b"x".to_vec()),
    ] {
        let root = put(&mut graph, &raw);
        let value = chunks::code_reference(&reference(&root, &bytes, offset))
            .unwrap()
            .unwrap();
        fail(chunks::read_code(&value, &mut |key| load(&graph, key)).unwrap_err());
    }
}

#[test]
fn canonicalization_reuses_immutable_refs_without_fetching_and_never_mutates_real_code() {
    let mut graph = Graph::new();
    let root = put(&mut graph, b"source");
    let cold = reference(&root, b"source", 0);
    let mut state = empty();
    state["tables"]["submissions"] = json!([
        {"id":"fetched","code":"source","finished_at":"2026-11-09"},
        {"id":"unfetched","code":"","finished_at":"2020-01-01"},
        {"id":"reference","code":cold,"finished_at":"2020-01-01"},
        {"id":"changed","code":"new local code","finished_at":"2026-11-09"}]);
    let before = state.clone();
    let known = [
        ("fetched".to_owned(), cold.clone()),
        ("unfetched".to_owned(), cold.clone()),
        ("changed".to_owned(), cold.clone()),
    ]
    .into_iter()
    .collect();
    let out = chunks::canonicalize_state(
        &state,
        &known,
        Utc.with_ymd_and_hms(2026, 11, 9, 12, 0, 0).unwrap(),
        &mut |_| panic!("known references do not rewrite or fetch objects"),
    )
    .unwrap();
    assert_eq!(state, before);
    assert!(out.code_references.is_empty());
    for row in &out.state["tables"]["submissions"].as_array().unwrap()[..3] {
        assert_eq!(row["code"], cold);
    }
    assert_eq!(
        out.state["tables"]["submissions"][3]["code"],
        "new local code"
    );
    let bad = [("fetched".to_owned(), format!("{CODE_PREFIX}{{}}"))]
        .into_iter()
        .collect();
    fail(chunks::canonicalize_state(&state, &bad, Utc::now(), &mut |_| Ok(())).unwrap_err());
}

#[test]
fn callback_errors_propagate_and_isolated_owner_graphs_do_not_share_cached_code() {
    let mut owner_a = Graph::new();
    let root = put(&mut owner_a, b"owner A synthetic code");
    let owner_b = Graph::new();
    assert_eq!(
        chunks::read_blob(&root, 100, &mut |key| load(&owner_b, key))
            .unwrap_err()
            .code,
        "SYNTHETIC_CACHE_MISS"
    );
    let stopped = ApiError::new(409, "ACCOUNT_EPOCH_CHANGED", "synthetic owner changed");
    assert_eq!(
        chunks::write_blob(b"new data", &[], &mut |_| Err(stopped.clone())).unwrap_err(),
        stopped
    );
    assert_eq!(
        chunks::read_blob(&root, 100, &mut |_| Err(stopped.clone())).unwrap_err(),
        stopped
    );
    let mut state = empty();
    state["tables"]["submissions"] =
        json!([{"id":"cold","code":"local remains","finished_at":"2020-01-01"}]);
    let before = state.clone();
    assert_eq!(
        chunks::canonicalize_state(&state, &BTreeMap::new(), Utc::now(), &mut |_| Err(
            stopped.clone()
        ))
        .unwrap_err(),
        stopped
    );
    assert_eq!(state, before);
    assert_eq!(
        chunks::read_blob(&root, 100, &mut |key| load(&owner_a, key)).unwrap(),
        b"owner A synthetic code"
    );
}

#[test]
fn submission_and_conflict_code_roots_remain_dependency_links_even_when_unfetched() {
    let mut graph = Graph::new();
    let cold_root = digest(b"cloud-only code");
    let cold = reference(&cold_root, b"not fetched", 0);
    let mut state = empty();
    state["tables"]["submissions"] = json!([{"id":"s","code":cold,"submitted_at":"2026-11"}]);
    state["tables"]["account_sync_conflicts"] =
        json!([{"id":"c","data":json!({"table":"submissions","row":{"code":cold}}).to_string()}]);
    let root = chunks::pack_state(&state, &mut |item| store(&mut graph, item)).unwrap();
    assert!(
        graph
            .values()
            .filter(|v| v.children.contains(&cold_root))
            .count()
            >= 2
    );
    assert!(!graph.contains_key(&cold_root));
    let unpacked = chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap();
    assert_eq!(
        unpacked.state["tables"]["submissions"],
        state["tables"]["submissions"]
    );
}

#[test]
fn malformed_manifest_table_sets_entries_roots_and_groups_fail_closed() {
    let mut graph = Graph::new();
    let profile = put(&mut graph, b"{}");
    let mut table_map = serde_json::Map::new();
    for &(table, _) in TABLES {
        table_map.insert(table.to_owned(), json!([]));
    }
    let base =
        json!({"format":"tb-private-chunk-state-v2","tables":table_map,"publicAccounts":profile});
    let mut candidates = Vec::new();
    let mut value = base.clone();
    value["tables"].as_object_mut().unwrap().remove("training");
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["extra"] = json!([]);
    candidates.push(value);
    let mut value = base.clone();
    value["extra"] = json!(0);
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["training"] = json!(false);
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["training"] = json!([{"bucket":"a","root":"bad"}]);
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["training"] = json!([{"bucket":"a","root":profile,"extra":0}]);
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["training"] =
        json!([{"bucket":"a","root":profile},{"bucket":"a","root":profile}]);
    candidates.push(value);
    let mut value = base.clone();
    value["tables"]["training"] = json!(
        (0..4097)
            .map(|i| json!({"bucket":i.to_string(),"root":profile}))
            .collect::<Vec<_>>()
    );
    candidates.push(value);
    for value in candidates {
        let root = put(&mut graph, &chunks::encode(&value).unwrap());
        fail(chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap_err());
    }
    let root = manifest_for(&mut graph, "training", &[json!({"id":"not-array"})]);
    fail(chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap_err());
    let oversized = put(&mut graph, &vec![b' '; chunks::MANIFEST_LIMIT + 1]);
    fail(chunks::unpack_state(&oversized, &mut |key| load(&graph, key)).unwrap_err());
}

#[test]
fn exact_dependency_and_bucket_capacities_remain_accepted() {
    let children = (0..256)
        .map(|i| digest(format!("link-{i}").as_bytes()))
        .collect();
    let item = object(ObjectKind::Data, gzip(b"bounded"), children);
    let wire = chunks::to_wire(&item).unwrap();
    assert_eq!(chunks::from_wire(&item.hash, &wire).unwrap(), item);
    assert_eq!(
        chunks::read_blob(&item.hash, 7, &mut |_| Ok(item.clone())).unwrap(),
        b"bounded"
    );
    let mut children = item.children.clone();
    children.push(digest(b"extra child"));
    let over = object(ObjectKind::Data, gzip(b"bounded"), children);
    fail(chunks::to_wire(&over).unwrap_err());
    let mut graph = Graph::new();
    let group = put(&mut graph, b"[]");
    let profile = put(&mut graph, b"{}");
    let mut tables = serde_json::Map::new();
    for &(table, _) in TABLES {
        tables.insert(table.to_owned(), json!([]));
    }
    tables.insert(
        "training".to_owned(),
        json!(
            (0..4096)
                .map(|i| json!({"bucket":i.to_string(),"root":group}))
                .collect::<Vec<_>>()
        ),
    );
    let root = put(
        &mut graph,
        &chunks::encode(
            &json!({"format":"tb-private-chunk-state-v2","tables":tables,"publicAccounts":profile}),
        )
        .unwrap(),
    );
    assert!(
        chunks::unpack_state(&root, &mut |key| load(&graph, key))
            .unwrap()
            .state["tables"]["training"]
            .as_array()
            .unwrap()
            .is_empty()
    );
}

#[test]
fn historical_code_has_a_real_262144_byte_boundary() {
    let now = Utc.with_ymd_and_hms(2026, 11, 9, 12, 0, 0).unwrap();
    let mut graph = Graph::new();
    let mut state = empty();
    state["tables"]["submissions"] =
        json!([{"id":"large","code":"x".repeat(chunks::CODE_LIMIT),"finished_at":"2020-01-01"}]);
    let projection = chunks::canonicalize_state(&state, &BTreeMap::new(), now, &mut |item| {
        store(&mut graph, item)
    })
    .unwrap();
    let reference = chunks::code_reference(
        projection.state["tables"]["submissions"][0]["code"]
            .as_str()
            .unwrap(),
    )
    .unwrap()
    .unwrap();
    assert_eq!(reference.bytes(), chunks::CODE_LIMIT);
    assert_eq!(
        chunks::read_code(&reference, &mut |key| load(&graph, key))
            .unwrap()
            .len(),
        chunks::CODE_LIMIT
    );
    state["tables"]["submissions"][0]["code"] = json!("x".repeat(chunks::CODE_LIMIT + 1));
    fail(
        chunks::canonicalize_state(&state, &BTreeMap::new(), now, &mut |_| {
            panic!("overlarge code fails before archiving")
        })
        .unwrap_err(),
    );
}

#[test]
#[ignore = "explicit 128 MiB blob / 512 MiB expanded-state boundary; run once for protocol delivery"]
fn real_capacity_boundaries_preserve_128_mib_and_reject_above_512_mib() {
    let mut graph = Graph::new();
    let mut raw = vec![b' '; chunks::RAW_LIMIT + 1];
    fail(
        chunks::write_blob(&raw, &[], &mut |_| {
            panic!("overlarge input fails before store")
        })
        .unwrap_err(),
    );
    raw.pop();
    raw[chunks::RAW_LIMIT - 2..].copy_from_slice(b"[]");
    let group = put(&mut graph, &raw);
    assert_eq!(
        chunks::read_blob(&group, chunks::RAW_LIMIT, &mut |key| load(&graph, key)).unwrap(),
        raw
    );
    drop(raw);
    let profile = put(&mut graph, b"{}");
    let mut tables = serde_json::Map::new();
    for &(table, _) in TABLES {
        tables.insert(table.to_owned(), json!([]));
    }
    // Large whitespace before [] exercises the real byte counter without making
    // huge row objects or putting hundreds of MiB into the committed fixtures.
    tables.insert(
        "training".to_owned(),
        json!(
            (0..4)
                .map(|i| json!({"bucket":i.to_string(),"root":group}))
                .collect::<Vec<_>>()
        ),
    );
    let root = put(
        &mut graph,
        &chunks::encode(
            &json!({"format":"tb-private-chunk-state-v2","tables":tables,"publicAccounts":profile}),
        )
        .unwrap(),
    );
    assert!(
        chunks::unpack_state(&root, &mut |key| load(&graph, key))
            .unwrap()
            .state["tables"]["training"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    tables["training"]
        .as_array_mut()
        .unwrap()
        .push(json!({"bucket":"4","root":group}));
    let root = put(
        &mut graph,
        &chunks::encode(
            &json!({"format":"tb-private-chunk-state-v2","tables":tables,"publicAccounts":profile}),
        )
        .unwrap(),
    );
    fail(chunks::unpack_state(&root, &mut |key| load(&graph, key)).unwrap_err());
}
