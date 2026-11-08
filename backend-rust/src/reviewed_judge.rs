//! Fixed, audited local cases. Python only authored the frozen public data.
//! The result remains local evidence, never an official AC or a reward grant.
use crate::{ApiError, native_judge::Case};
use flate2::bufread::GzDecoder;
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, io::Read, sync::OnceLock};

pub const SOURCE_SHA256: &str = "20fd6a302157ff9b9cefb757a5bda9d287fde6d23aed37a83a07a8e8fb3b7741";
const MIB: usize = 1024 * 1024;
const BLOCK: usize = 65536;
const MAX_RAW: usize = 64 * MIB;
const MAX_INPUT: usize = 32 * MIB;
const LEGACY_OUTPUT: usize = 32 * MIB;

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
pub enum Checker {
    Exact,
    Inequality,
    Gcd,
}

pub struct ReviewedSuite {
    pub profile_id: &'static str,
    pub coverage: &'static str,
    pub source_sha256: &'static str,
    pub cases: Vec<Case>,
    pub checker: Checker,
    /// Aggregate output budget including a 1 MiB original-sample allowance.
    /// This does not change ordinary samples or custom-input limits.
    pub max_output_bytes: usize,
}

#[derive(Deserialize)]
struct Manifest {
    schema: u32,
    source_sha256: String,
    seed: u32,
    production_executes_python: bool,
    original_samples_included: bool,
    profiles: Vec<Profile>,
}
#[derive(Clone, Deserialize)]
struct Profile {
    profile_id: String,
    coverage: String,
    checker: Checker,
    compressed_bytes: usize,
    compressed_sha256: String,
    raw_bytes: usize,
    raw_sha256: String,
    case_count: usize,
    input_bytes: usize,
    expected_output_bytes: usize,
    max_input_bytes: usize,
    max_expected_output_bytes: usize,
    canonical_extra_output_bound_bytes: usize,
    max_output_bytes: usize,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Fixture {
    schema: u32,
    profile_id: String,
    source_sha256: String,
    seed: u32,
    checker: Checker,
    cases: Vec<FrozenCase>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct FrozenCase {
    name: String,
    input: String,
    output: String,
}

include!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/resources/reviewed_cases/packs.rs"
));

fn corrupt() -> ApiError {
    ApiError::new(
        500,
        "REVIEWED_CASES_INVALID",
        "本地审核用例校验失败，代码已保留",
    )
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn manifest() -> Result<&'static Manifest, ApiError> {
    static MANIFEST: OnceLock<Result<Manifest, ()>> = OnceLock::new();
    MANIFEST
        .get_or_init(|| {
            let value: Manifest = serde_json::from_str(include_str!(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/resources/reviewed_cases/manifest.json"
            )))
            .map_err(|_| ())?;
            let mut seen = std::collections::BTreeSet::new();
            if value.schema != 1
                || value.source_sha256 != SOURCE_SHA256
                || value.seed != 20261008
                || value.production_executes_python
                || value.original_samples_included
                || value.profiles.len() != 15
                || value.profiles.iter().any(|p| {
                    !seen.insert(&p.profile_id)
                        || packed_bytes(&p.profile_id).is_none()
                        || p.coverage.is_empty()
                        || p.coverage.len() > 4096
                        || !(1..=200).contains(&p.case_count)
                        || !(1..=MAX_RAW).contains(&p.raw_bytes)
                        || !(1..=MAX_INPUT).contains(&p.max_input_bytes)
                        || !(MIB..=LEGACY_OUTPUT).contains(&p.max_output_bytes)
                })
            {
                return Err(());
            }
            Ok(value)
        })
        .as_ref()
        .map_err(|_| corrupt())
}

fn output_bound(case: &FrozenCase, checker: Checker) -> Option<usize> {
    match checker {
        Checker::Inequality if case.output.split_whitespace().next()? == "Yes" => {
            let n = case
                .input
                .split_whitespace()
                .next()?
                .parse::<usize>()
                .ok()?;
            (1..=200000)
                .contains(&n)
                .then(|| 4 + n * (n.to_string().len() + 1))
        }
        Checker::Gcd => case
            .input
            .split_whitespace()
            .next()?
            .parse::<usize>()
            .ok()?
            .checked_mul(40),
        _ => Some(case.output.len()),
    }
}

fn decode(profile: &Profile, bytes: &[u8]) -> Result<Vec<Case>, ApiError> {
    if bytes.len() != profile.compressed_bytes || digest(bytes) != profile.compressed_sha256 {
        return Err(corrupt());
    }
    // Exact-size allocation plus a one-byte EOF probe prevents a gzip bomb or
    // concatenated member from growing the bound. The raw buffer is dropped
    // immediately after parsing; only this selected profile stays in memory.
    let mut decoder = GzDecoder::new(bytes);
    let mut raw = vec![0; profile.raw_bytes];
    decoder.read_exact(&mut raw).map_err(|_| corrupt())?;
    let mut extra = [0];
    if decoder.read(&mut extra).map_err(|_| corrupt())? != 0
        || !decoder.get_ref().is_empty()
        || digest(&raw) != profile.raw_sha256
    {
        return Err(corrupt());
    }
    let fixture: Fixture = serde_json::from_slice(&raw).map_err(|_| corrupt())?;
    drop(raw);
    if fixture.schema != 1
        || fixture.profile_id != profile.profile_id
        || fixture.source_sha256 != SOURCE_SHA256
        || fixture.seed != 20261008
        || fixture.checker != profile.checker
        || fixture.cases.len() != profile.case_count
    {
        return Err(corrupt());
    }
    let mut input = 0usize;
    let mut output = 0usize;
    let mut bound = 0usize;
    let mut max_input = 0;
    let mut max_output = 0;
    for case in &fixture.cases {
        if case.name.is_empty() || case.name.len() > 1024 || case.input.len() > MAX_INPUT {
            return Err(corrupt());
        }
        input = input.checked_add(case.input.len()).ok_or_else(corrupt)?;
        output = output.checked_add(case.output.len()).ok_or_else(corrupt)?;
        bound = bound
            .checked_add(output_bound(case, profile.checker).ok_or_else(corrupt)?)
            .ok_or_else(corrupt)?;
        max_input = max_input.max(case.input.len());
        max_output = max_output.max(case.output.len());
    }
    let budget = MIB + bound.div_ceil(BLOCK) * BLOCK;
    if input != profile.input_bytes
        || output != profile.expected_output_bytes
        || max_input != profile.max_input_bytes
        || max_output != profile.max_expected_output_bytes
        || bound != profile.canonical_extra_output_bound_bytes
        || budget != profile.max_output_bytes
        || budget > LEGACY_OUTPUT
    {
        return Err(corrupt());
    }
    Ok(fixture
        .cases
        .into_iter()
        .map(|c| Case {
            name: c.name,
            input: c.input,
            expected: Some(c.output),
        })
        .collect())
}

pub fn build(identity: &str) -> Result<Option<ReviewedSuite>, ApiError> {
    let Some(bytes) = packed_bytes(identity) else {
        return Ok(None);
    };
    let profile = manifest()?
        .profiles
        .iter()
        .find(|p| p.profile_id == identity)
        .ok_or_else(corrupt)?;
    Ok(Some(ReviewedSuite {
        profile_id: &profile.profile_id,
        coverage: &profile.coverage,
        source_sha256: SOURCE_SHA256,
        cases: decode(profile, bytes)?,
        checker: profile.checker,
        max_output_bytes: profile.max_output_bytes,
    }))
}

fn inequality(input: &str, actual: &str, expected: &str) -> bool {
    let mut source = input.split_whitespace();
    let Some(n) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
        return false;
    };
    let Some(q) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
        return false;
    };
    if !(1..=200000).contains(&n) || q > 200000 {
        return false;
    }
    let possible = match expected.split_whitespace().next() {
        Some("Yes") => true,
        Some("No") => false,
        _ => return false,
    };
    let mut answer = actual.split_whitespace();
    let yes = match answer.next() {
        Some("Yes") if possible => true,
        Some("No") if !possible => false,
        _ => return false,
    };
    let mut values = Vec::with_capacity(if yes { n } else { 0 });
    if yes {
        for _ in 0..n {
            let Some(v) = answer.next().and_then(|s| s.parse::<usize>().ok()) else {
                return false;
            };
            if !(1..=n).contains(&v) {
                return false;
            }
            values.push(v);
        }
    }
    if answer.next().is_some() {
        return false;
    }
    for _ in 0..q {
        let Some(t) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
            return false;
        };
        let Some(u) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
            return false;
        };
        let Some(v) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
            return false;
        };
        if t > 1
            || !(1..=n).contains(&u)
            || !(1..=n).contains(&v)
            || yes && values[u - 1] + t > values[v - 1]
        {
            return false;
        }
    }
    source.next().is_none()
}

fn gcd(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}
fn maximum_gcd(x: u64, y: u64) -> u128 {
    let mut factors = BTreeMap::<u64, u32>::new();
    for mut value in [x, y] {
        let mut p = 2;
        while p <= value / p {
            while value % p == 0 {
                *factors.entry(p).or_default() += 1;
                value /= p;
            }
            p += if p == 2 { 1 } else { 2 };
        }
        if value > 1 {
            *factors.entry(value).or_default() += 1;
        }
    }
    factors
        .into_iter()
        .map(|(p, count)| (p as u128).pow(count / 2))
        .product()
}
fn gcd_construction(input: &str, actual: &str) -> bool {
    let mut source = input.split_whitespace();
    let Some(tests) = source.next().and_then(|s| s.parse::<usize>().ok()) else {
        return false;
    };
    let mut answer = actual.split_whitespace();
    for _ in 0..tests {
        let Some(x) = source.next().and_then(|s| s.parse::<u64>().ok()) else {
            return false;
        };
        let Some(y) = source.next().and_then(|s| s.parse::<u64>().ok()) else {
            return false;
        };
        let Some(a) = answer.next().and_then(|s| s.parse::<u128>().ok()) else {
            return false;
        };
        let Some(b) = answer.next().and_then(|s| s.parse::<u128>().ok()) else {
            return false;
        };
        if !(1..=1_000_000_000).contains(&x)
            || !(1..=1_000_000_000).contains(&y)
            || !(1..=1_000_000_000_000_000_000).contains(&a)
            || !(1..=1_000_000_000_000_000_000).contains(&b)
            || a * b != x as u128 * y as u128
            || gcd(a, b) != maximum_gcd(x, y)
        {
            return false;
        }
    }
    source.next().is_none() && answer.next().is_none()
}

/// No process, network, source evaluation or account state is consulted.
pub fn check(checker: Checker, input: &str, actual: &str, expected: &str) -> bool {
    match checker {
        Checker::Exact => actual.split_whitespace().eq(expected.split_whitespace()),
        Checker::Inequality => inequality(input, actual, expected),
        Checker::Gcd => gcd_construction(input, actual),
    }
}

#[cfg(test)]
mod source_guards {
    use super::*;
    use flate2::{Compression, write::GzEncoder};
    use std::io::Write;

    fn small() -> (Profile, Vec<u8>) {
        let p = manifest()
            .unwrap()
            .profiles
            .iter()
            .find(|p| p.profile_id == "入门赛 49::D")
            .unwrap()
            .clone();
        let bytes = packed_bytes(&p.profile_id).unwrap().to_vec();
        (p, bytes)
    }
    fn describe(p: &mut Profile, raw: &[u8]) -> Vec<u8> {
        let mut compressor = GzEncoder::new(Vec::new(), Compression::default());
        compressor.write_all(raw).unwrap();
        let bytes = compressor.finish().unwrap();
        p.raw_bytes = raw.len();
        p.raw_sha256 = digest(raw);
        p.compressed_bytes = bytes.len();
        p.compressed_sha256 = digest(&bytes);
        bytes
    }
    #[test]
    fn corrupt_truncated_and_concatenated_archives_never_produce_cases() {
        let (p, bytes) = small();
        let mut corrupt_bytes = bytes.clone();
        corrupt_bytes[10] ^= 1;
        assert!(decode(&p, &corrupt_bytes).is_err());
        for bad in [
            &bytes[..bytes.len() - 4],
            &[bytes.as_slice(), b"trailing"].concat(),
        ] {
            let mut metadata = p.clone();
            metadata.compressed_bytes = bad.len();
            metadata.compressed_sha256 = digest(bad);
            assert!(decode(&metadata, bad).is_err());
        }
    }
    #[test]
    fn inflated_length_and_output_budget_cannot_be_silently_weakened() {
        let (p, bytes) = small();
        let mut short = p.clone();
        short.raw_bytes -= 1;
        assert!(decode(&short, &bytes).is_err());
        let mut budget = p;
        budget.max_output_bytes -= BLOCK;
        assert!(decode(&budget, &bytes).is_err());
    }
    #[test]
    fn valid_gzip_and_hashes_do_not_excuse_wrong_source_or_identity() {
        let (p, bytes) = small();
        let mut raw = String::new();
        GzDecoder::new(bytes.as_slice())
            .read_to_string(&mut raw)
            .unwrap();
        for (field, value) in [
            ("profile_id", "入门赛 49::E"),
            ("source_sha256", "unreviewed"),
        ] {
            let mut document: serde_json::Value = serde_json::from_str(&raw).unwrap();
            document[field] = value.into();
            let raw = serde_json::to_vec(&document).unwrap();
            let mut metadata = p.clone();
            let changed = describe(&mut metadata, &raw);
            assert!(decode(&metadata, &changed).is_err());
        }
    }
}
