use reqwest::Method;
use serde_json::{Value, json};
use std::{
    collections::VecDeque,
    io::{Read, Write},
    net::TcpListener,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
use tobe_core::account_transport::{AccountTransport, Credentials, Request, validate_endpoint};

#[derive(Clone)]
struct Reply {
    status: u16,
    body: Vec<u8>,
    headers: String,
    delay: Duration,
    drop_response: bool,
    declared: Option<usize>,
}
impl Reply {
    fn json(value: Value) -> Self {
        Self {
            status: 200,
            body: value.to_string().into_bytes(),
            headers: String::new(),
            delay: Duration::ZERO,
            drop_response: false,
            declared: None,
        }
    }
}
struct Server {
    endpoint: String,
    received: Arc<Mutex<Vec<(String, Vec<u8>)>>>,
    stop: Arc<AtomicBool>,
    worker: Option<JoinHandle<()>>,
}
impl Server {
    fn new(replies: Vec<Reply>) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        listener.set_nonblocking(true).unwrap();
        let endpoint = format!("http://{}", listener.local_addr().unwrap());
        let received = Arc::new(Mutex::new(vec![]));
        let seen = received.clone();
        let stop = Arc::new(AtomicBool::new(false));
        let halted = stop.clone();
        let worker = thread::spawn(move || {
            let mut replies = VecDeque::from(replies);
            while !halted.load(Ordering::SeqCst) {
                match listener.accept() {
                    Ok((mut stream, _)) => {
                        stream.set_nonblocking(false).unwrap();
                        stream
                            .set_read_timeout(Some(Duration::from_secs(2)))
                            .unwrap();
                        let mut raw = vec![];
                        let mut byte = [0; 1];
                        while !raw.ends_with(b"\r\n\r\n") && raw.len() < 65536 {
                            if stream.read(&mut byte).unwrap_or(0) == 0 {
                                break;
                            }
                            raw.push(byte[0]);
                        }
                        let header = String::from_utf8(raw).unwrap();
                        let size = header
                            .lines()
                            .find_map(|line| {
                                line.to_lowercase()
                                    .strip_prefix("content-length:")
                                    .and_then(|n| n.trim().parse::<usize>().ok())
                            })
                            .unwrap_or(0);
                        let mut body = vec![0; size];
                        if stream.read_exact(&mut body).is_err() {
                            continue;
                        }
                        seen.lock().unwrap().push((header, body));
                        let reply = replies
                            .pop_front()
                            .unwrap_or_else(|| Reply::json(json!({"unexpected":true})));
                        if reply.drop_response {
                            continue;
                        }
                        thread::sleep(reply.delay);
                        let header = format!(
                            "HTTP/1.1 {} Test\r\nContent-Length: {}\r\nConnection: close\r\n{}\r\n",
                            reply.status,
                            reply.declared.unwrap_or(reply.body.len()),
                            reply.headers
                        );
                        let _ = stream.write_all(header.as_bytes());
                        let _ = stream.write_all(&reply.body);
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(Duration::from_millis(3))
                    }
                    Err(_) => break,
                }
            }
        });
        Self {
            endpoint,
            received,
            stop,
            worker: Some(worker),
        }
    }
    fn count(&self) -> usize {
        self.received.lock().unwrap().len()
    }
    fn wait(&self) {
        let start = Instant::now();
        while self.count() == 0 {
            assert!(start.elapsed() < Duration::from_secs(2));
            thread::sleep(Duration::from_millis(3));
        }
    }
}
impl Drop for Server {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        if let Some(worker) = self.worker.take() {
            worker.join().unwrap();
        }
    }
}
fn request(method: Method) -> Request<'static> {
    Request {
        method,
        path: "/v1/accounts/state",
        body: None,
        credentials: Some(Credentials {
            owner: "generated-owner",
            bearer: "generated-fixture-bearer-not-a-real-token",
        }),
        state_revision: Some(7),
        maximum: 262144,
        timeout: Duration::from_secs(1),
    }
}

#[test]
fn configured_endpoints_match_the_real_legacy_validator_and_keep_loopback_exception_narrow() {
    let values = [
        "",
        " https://example.test/ ",
        "https://example.test:443/base",
        "http://127.0.0.1:54321",
        "http://localhost:54321/path",
        "http://[::1]:54321/path",
        "http://127.0.0.2:54321",
        "http://example.test",
        "https://user:password@example.test",
        "https://example.test:444",
        "https://example.test/?secret=x",
        "https://example.test/#token",
    ];
    let actual = values
        .iter()
        .map(|v| match validate_endpoint(v) {
            Ok(value) => json!({"ok":true,"value":value}),
            Err(error) => json!({"ok":false,"status":error.status}),
        })
        .collect::<Vec<_>>();
    let python = std::env::var("TB_NATIVE_TEST_PYTHON").unwrap();
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let script = "import json,sys\nfrom pathlib import Path\nr=Path(sys.argv[1]);sys.path[:0]=[str(r/'backend'),str(r/'backend/common')]\nfrom leaderboard import validate_endpoint\nfrom training import ServiceError\nresult=[]\nfor value in json.load(sys.stdin):\n try:result.append({'ok':True,'value':validate_endpoint(value)})\n except ServiceError as e:result.append({'ok':False,'status':e.status})\njson.dump(result,sys.stdout)\n";
    let mut child = std::process::Command::new(python)
        .args(["-c", script])
        .arg(root)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(json!(values).to_string().as_bytes())
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    assert_eq!(
        json!(actual),
        serde_json::from_slice::<Value>(&output.stdout).unwrap()
    );
    assert!(validate_endpoint("https://example.test/\r\nheader").is_err());
}

#[test]
fn real_http_uses_the_exact_owned_state_and_chunk_headers_and_rejects_stale_work_before_io() {
    let server = Server::new(vec![Reply::json(
        json!({"owner":"generated-owner","revision":7}),
    )]);
    let client = AccountTransport::new().unwrap();
    assert_eq!(
        client
            .request(&server.endpoint, request(Method::GET), &|| false)
            .unwrap_err()
            .code,
        "OWNER_CHANGED"
    );
    assert_eq!(server.count(), 0);
    let value = client
        .request(&server.endpoint, request(Method::GET), &|| true)
        .unwrap();
    assert_eq!(value["revision"], 7);
    let received = server.received.lock().unwrap();
    let header = received[0].0.to_lowercase();
    for text in [
        "get /v1/accounts/state ",
        "x-tb-user: generated-owner",
        "authorization: bearer generated-fixture-bearer-not-a-real-token",
        "x-tb-state-protocol: 1",
        "x-tb-chunk-protocol: 2",
        "x-tb-state-revision: 7",
    ] {
        assert!(header.contains(text));
    }
    assert!(received[0].1.is_empty());
}

#[test]
fn lost_write_acknowledgements_never_replay_on_another_route_or_under_reqwest_retry() {
    let mut reply = Reply::json(json!({}));
    reply.drop_response = true;
    let server = Server::new(vec![reply]);
    let client = AccountTransport::new().unwrap();
    let body = json!({"loginId":"generated_user","password":"generated-not-a-real-password"});
    let mut spec = request(Method::POST);
    spec.path = "/v1/accounts/login";
    spec.body = Some(&body);
    let error = client
        .request(&server.endpoint, spec, &|| true)
        .unwrap_err();
    assert_eq!(error.code, "ACCOUNT_CONNECTION_UNAVAILABLE");
    assert!(error.uncertain);
    assert!(!error.retryable);
    thread::sleep(Duration::from_millis(80));
    assert_eq!(server.count(), 1);
    let received = server.received.lock().unwrap();
    assert_eq!(
        serde_json::from_slice::<Value>(&received[0].1).unwrap(),
        body
    );
}

#[test]
fn redirects_never_forward_account_authority_to_the_target() {
    let target = Server::new(vec![]);
    let mut reply = Reply::json(json!({}));
    reply.status = 302;
    reply.headers = format!("Location: {}/v1/profile\r\n", target.endpoint);
    let server = Server::new(vec![reply]);
    let client = AccountTransport::new().unwrap();
    assert_eq!(
        client
            .request(&server.endpoint, request(Method::GET), &|| true)
            .unwrap_err()
            .code,
        "ACCOUNT_REDIRECT_REJECTED"
    );
    assert_eq!(server.count(), 1);
    assert_eq!(target.count(), 0);
}

#[test]
fn malformed_success_is_not_an_offline_lease_and_oversize_bodies_are_bounded() {
    let mut invalid = Reply::json(json!({}));
    invalid.body = b"invalid-json".to_vec();
    let mut oversized = Reply::json(json!({}));
    oversized.declared = Some(1000000);
    let mut truncated = Reply::json(json!({"missing":"body"}));
    truncated.declared = Some(truncated.body.len() + 20);
    let server = Server::new(vec![invalid, Reply::json(json!([])), oversized, truncated]);
    let client = AccountTransport::new().unwrap();
    for _ in 0..4 {
        assert_eq!(
            client
                .request(&server.endpoint, request(Method::GET), &|| true)
                .unwrap_err()
                .code,
            "ACCOUNT_RESPONSE_INVALID"
        );
    }
    assert_eq!(server.count(), 4);
}

#[test]
fn an_owner_switch_during_the_response_and_the_absolute_deadline_prevent_late_application() {
    let mut reply = Reply::json(json!({"secret":"generated response"}));
    reply.delay = Duration::from_millis(100);
    let server = Server::new(vec![reply.clone()]);
    let current = Arc::new(AtomicBool::new(true));
    let active = current.clone();
    let endpoint = server.endpoint.clone();
    let worker = thread::spawn(move || {
        AccountTransport::new()
            .unwrap()
            .request(&endpoint, request(Method::GET), &|| {
                active.load(Ordering::SeqCst)
            })
    });
    server.wait();
    current.store(false, Ordering::SeqCst);
    assert_eq!(worker.join().unwrap().unwrap_err().code, "OWNER_CHANGED");
    reply.delay = Duration::from_millis(300);
    let server = Server::new(vec![reply]);
    let client = AccountTransport::new().unwrap();
    let mut spec = request(Method::GET);
    spec.timeout = Duration::from_millis(75);
    let start = Instant::now();
    assert_eq!(
        client
            .request(&server.endpoint, spec, &|| true)
            .unwrap_err()
            .code,
        "ACCOUNT_CONNECTION_UNAVAILABLE"
    );
    assert!(start.elapsed() < Duration::from_millis(500));
    assert_eq!(server.count(), 1);
}

#[test]
fn definite_http_auth_rejection_keeps_its_status_and_error_bodies_never_echo_credentials() {
    let mut auth = Reply::json(json!({}));
    auth.status = 401;
    auth.declared = Some(1000000);
    let mut secret = Reply::json(json!({"error":"leaked generated-not-a-real-password"}));
    secret.status = 400;
    let server = Server::new(vec![auth, secret]);
    let client = AccountTransport::new().unwrap();
    let error = client
        .request(&server.endpoint, request(Method::GET), &|| true)
        .unwrap_err();
    assert_eq!(error.status, 401);
    assert_eq!(error.code, "ACCOUNT_AUTH_REJECTED");
    let body = json!({"password":"generated-not-a-real-password"});
    let mut spec = request(Method::POST);
    spec.body = Some(&body);
    let error = client
        .request(&server.endpoint, spec, &|| true)
        .unwrap_err();
    assert_eq!(error.status, 400);
    assert!(!error.message.contains("generated-not-a-real-password"));
}
