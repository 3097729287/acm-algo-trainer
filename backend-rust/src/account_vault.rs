//! Windows current-user DPAPI, compatible with the existing encrypted session
//! document. No password, bearer, or decrypted session is persisted as JSON.
use crate::{ApiError, local_documents::Documents};
use base64::{Engine, engine::general_purpose::STANDARD};
use serde_json::{Value, json};
use std::path::Path;

const SESSION: &str = "account-session.json";
const MAX_PLAINTEXT: usize = 1024 * 1024;
const MAX_CIPHERTEXT: usize = 2 * 1024 * 1024;
fn failed() -> ApiError {
    ApiError::new(
        503,
        "CREDENTIAL_PROTECTION_FAILED",
        "本机登录凭据无法读取或保护，请重新登录；原记录已保留",
    )
}
fn crypt(data: &[u8], decrypt: bool) -> Result<Vec<u8>, ApiError> {
    if data.len()
        > if decrypt {
            MAX_CIPHERTEXT
        } else {
            MAX_PLAINTEXT
        }
    {
        return Err(failed());
    }
    platform_crypt(data, decrypt)
}
#[cfg(windows)]
fn platform_crypt(data: &[u8], decrypt: bool) -> Result<Vec<u8>, ApiError> {
    use windows_sys::Win32::{
        Foundation::LocalFree,
        Security::Cryptography::{
            CRYPT_INTEGER_BLOB, CRYPTPROTECT_UI_FORBIDDEN, CryptProtectData, CryptUnprotectData,
        },
    };
    let input = CRYPT_INTEGER_BLOB {
        cbData: data.len() as u32,
        pbData: data.as_ptr() as *mut u8,
    };
    let mut output = CRYPT_INTEGER_BLOB::default();
    let success = unsafe {
        if decrypt {
            CryptUnprotectData(
                &input,
                std::ptr::null_mut(),
                std::ptr::null(),
                std::ptr::null(),
                std::ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        } else {
            CryptProtectData(
                &input,
                std::ptr::null(),
                std::ptr::null(),
                std::ptr::null(),
                std::ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        }
    };
    struct Guard(*mut u8);
    impl Drop for Guard {
        fn drop(&mut self) {
            if !self.0.is_null() {
                unsafe {
                    LocalFree(self.0.cast());
                }
            }
        }
    }
    let _guard = Guard(output.pbData);
    if success == 0
        || output.cbData as usize > MAX_CIPHERTEXT
        || output.pbData.is_null() && output.cbData != 0
    {
        return Err(failed());
    }
    if output.cbData == 0 {
        return Ok(vec![]);
    }
    Ok(unsafe { std::slice::from_raw_parts(output.pbData, output.cbData as usize) }.to_vec())
}
#[cfg(not(windows))]
fn platform_crypt(_data: &[u8], _decrypt: bool) -> Result<Vec<u8>, ApiError> {
    Err(ApiError::new(
        422,
        "CREDENTIAL_PLATFORM_UNSUPPORTED",
        "此系统尚未接入本机凭据保护，不写入明文",
    ))
}

pub struct SessionVault {
    documents: Documents,
}
impl SessionVault {
    pub fn new(root: &Path) -> Self {
        Self {
            documents: Documents::new(root),
        }
    }
    pub fn read(&self) -> Result<Option<Vec<u8>>, ApiError> {
        let value = self.documents.load(SESSION, json!(""))?;
        let encoded = value.as_str().ok_or_else(failed)?;
        if encoded.is_empty() {
            return Ok(None);
        }
        if encoded.len() > MAX_CIPHERTEXT * 4 / 3 + 4 {
            return Err(failed());
        }
        let ciphertext = STANDARD.decode(encoded).map_err(|_| failed())?;
        let plaintext = crypt(&ciphertext, true)?;
        if plaintext.len() > MAX_PLAINTEXT {
            return Err(failed());
        }
        Ok(Some(plaintext))
    }
    pub fn write(&self, plaintext: &[u8]) -> Result<(), ApiError> {
        let ciphertext = crypt(plaintext, false)?;
        self.documents
            .save(SESSION, &Value::String(STANDARD.encode(ciphertext)))
    }
    pub fn clear(&self) -> Result<(), ApiError> {
        self.documents.save(SESSION, &json!(""))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::local_documents::Documents;
    use rusqlite::Connection;
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    fn python_crypt(data: &[u8], decrypt: bool) -> Vec<u8> {
        let python = std::env::var("TB_NATIVE_TEST_PYTHON")
            .expect("Use scripts/native.ps1 -Action test -TestPython ...");
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap();
        let script = "import base64,json,sys\nfrom pathlib import Path\nr=Path(sys.argv[1]);sys.path[:0]=[str(r/'backend'),str(r/'backend/common')]\nfrom translation_config import _crypt\nv=json.load(sys.stdin);sys.stdout.write(base64.b64encode(_crypt(base64.b64decode(v['data']),decrypt=v['decrypt'])).decode('ascii'))\n";
        let mut child = Command::new(python)
            .args(["-c", script])
            .arg(root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(
                json!({"data":STANDARD.encode(data),"decrypt":decrypt})
                    .to_string()
                    .as_bytes(),
            )
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "Legacy DPAPI fixture failed without exposing credential contents"
        );
        STANDARD.decode(output.stdout).unwrap()
    }
    #[test]
    fn legacy_documents_import_one_key_and_preserve_the_file_and_every_other_record() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("account-workspaces.json");
        let raw=b"\xef\xbb\xbf{\"activeOwner\":\"generated-fixture\",\"unknownFuture\":{\"preserve\":true}}";
        std::fs::write(&path, raw).unwrap();
        let docs = Documents::new(temp.path());
        docs.save("other-settings.json", &json!({"theme":"dark"}))
            .unwrap();
        let registry = docs.load("account-workspaces.json", json!({})).unwrap();
        assert_eq!(registry["unknownFuture"]["preserve"], true);
        assert_eq!(std::fs::read(path).unwrap(), raw);
        assert_eq!(
            docs.load("other-settings.json", Value::Null).unwrap(),
            json!({"theme":"dark"})
        );
        docs.save(
            "account-workspaces.json",
            &json!({"activeOwner":"another-fixture"}),
        )
        .unwrap();
        assert_eq!(
            docs.load("other-settings.json", Value::Null).unwrap(),
            json!({"theme":"dark"})
        );
    }
    #[test]
    fn foreign_or_corrupt_documents_do_not_overwrite_originals_or_create_other_keys() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("tb-documents.sqlite3");
        let db = Connection::open(&path).unwrap();
        db.execute_batch("CREATE TABLE drafts(code TEXT);INSERT INTO drafts VALUES('untouched')")
            .unwrap();
        drop(db);
        let before = std::fs::read(&path).unwrap();
        let docs = Documents::new(temp.path());
        assert_eq!(
            docs.save("account-session.json", &json!("ciphertext"))
                .unwrap_err()
                .code,
            "DOCUMENT_STORE_COLLISION"
        );
        assert_eq!(
            docs.load("account-session.json", Value::Null)
                .unwrap_err()
                .code,
            "DOCUMENT_STORE_COLLISION"
        );
        assert_eq!(std::fs::read(&path).unwrap(), before);
        assert!(docs.save("../account-session.json", &json!("bad")).is_err());
        let temp = tempfile::tempdir().unwrap();
        let docs = Documents::new(temp.path());
        docs.save("account-session.json", &json!("original"))
            .unwrap();
        let db = Connection::open(temp.path().join("tb-documents.sqlite3")).unwrap();
        db.execute(
            "UPDATE documents SET value='invalid-json' WHERE key='account-session.json'",
            [],
        )
        .unwrap();
        drop(db);
        assert_eq!(
            docs.load("account-session.json", Value::Null)
                .unwrap_err()
                .code,
            "INVALID_LOCAL_DOCUMENT"
        );
        let db = Connection::open(temp.path().join("tb-documents.sqlite3")).unwrap();
        assert_eq!(
            db.query_row(
                "SELECT value FROM documents WHERE key='account-session.json'",
                [],
                |r| r.get::<_, String>(0)
            )
            .unwrap(),
            "invalid-json"
        );
    }
    #[cfg(windows)]
    #[test]
    fn dpapi_roundtrips_generated_unicode_bytes_with_the_real_legacy_implementation_in_both_directions()
     {
        let plaintext = "Generated test token only 😀\0原生会话互通".as_bytes();
        let native = crypt(plaintext, false).unwrap();
        assert!(
            !native
                .windows(plaintext.len())
                .any(|part| part == plaintext)
        );
        assert!(python_crypt(&native, true) == plaintext);
        let legacy = python_crypt(plaintext, false);
        assert!(crypt(&legacy, true).unwrap() == plaintext);
        assert!(crypt(&native, true).unwrap() == plaintext);
    }
    #[cfg(windows)]
    #[test]
    fn protected_session_documents_reopen_clear_and_keep_registry_without_plaintext_storage() {
        let temp = tempfile::tempdir().unwrap();
        let vault = SessionVault::new(temp.path());
        let plaintext = b"generated-fixture-bearer-never-a-real-token";
        assert!(vault.read().unwrap().is_none());
        vault.write(plaintext).unwrap();
        Documents::new(temp.path())
            .save("account-workspaces.json", &json!({"activeOwner":"fixture"}))
            .unwrap();
        let raw = std::fs::read(temp.path().join("tb-documents.sqlite3")).unwrap();
        assert!(!raw.windows(plaintext.len()).any(|part| part == plaintext));
        assert!(SessionVault::new(temp.path()).read().unwrap().unwrap() == plaintext);
        vault.clear().unwrap();
        assert!(vault.read().unwrap().is_none());
        assert_eq!(
            Documents::new(temp.path())
                .load("account-workspaces.json", Value::Null)
                .unwrap(),
            json!({"activeOwner":"fixture"})
        );
    }
    #[cfg(windows)]
    #[test]
    fn broken_or_oversized_ciphertexts_never_fall_back_to_plaintext_or_replace_the_document() {
        let temp = tempfile::tempdir().unwrap();
        let docs = Documents::new(temp.path());
        let vault = SessionVault::new(temp.path());
        docs.save(SESSION, &json!("plain text is not a credential"))
            .unwrap();
        assert_eq!(
            vault.read().unwrap_err().code,
            "CREDENTIAL_PROTECTION_FAILED"
        );
        assert_eq!(
            docs.load(SESSION, Value::Null).unwrap(),
            json!("plain text is not a credential")
        );
        let value = json!(STANDARD.encode(b"truncated protected input"));
        docs.save(SESSION, &value).unwrap();
        assert!(vault.read().is_err());
        assert_eq!(docs.load(SESSION, Value::Null).unwrap(), value);
        assert!(vault.write(&vec![0; MAX_PLAINTEXT + 1]).is_err());
        assert_eq!(docs.load(SESSION, Value::Null).unwrap(), value);
    }
}
