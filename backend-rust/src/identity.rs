//! First-party problem identity rules shared with backend/insights.py.
use percent_encoding::percent_decode_str;
use regex::Regex;
use std::sync::LazyLock;

static CF: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^/(?:contest/(\d+)/problem|problemset/problem/(\d+))/([A-Za-z0-9]+)$").unwrap()
});
static GYM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^/gym/(\d+)/problem/([A-Za-z0-9]+)$").unwrap());
static AT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^/contests/([\w-]+)/tasks/([\w-]+)$").unwrap());
static LG: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^/problem/([A-Za-z]+\d+)$").unwrap());
static NC: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^/acm/contest/(\d+)/([A-Za-z0-9]+)$").unwrap());
static QOJ: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^/(?:contest/\d+/)?problem/(\d+)(?:/statement/(?:default|zh_cn))?$").unwrap()
});
static SPOJ: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^/problems/[A-Za-z0-9_]+$").unwrap());

pub fn canonical_url(value: &str) -> Option<String> {
    let value = value.trim();
    let parsed = url::Url::parse(value).ok()?;
    // Keep the supplied path; URL parsing must not collapse dot segments into
    // another problem identity. Decode once, as urllib.parse.unquote does.
    let remainder = value.split_once("://")?.1;
    let start = remainder.find(['/', '?', '#']).unwrap_or(remainder.len());
    let authority = remainder[..start].rsplit('@').next()?;
    let host = if authority.starts_with('[') {
        authority.strip_prefix('[')?.split_once(']')?.0
    } else {
        authority.split(':').next()?
    };
    let host = host.to_lowercase();
    let host = host.strip_prefix("www.").unwrap_or(&host);
    let path = remainder[start..].split(['?', '#']).next().unwrap_or("");
    let path = percent_decode_str(path).decode_utf8_lossy();
    let path = path.trim_end_matches('/');
    if ["codeforces.com", "m1.codeforces.com", "m2.codeforces.com"].contains(&host) {
        if let Some(c) = CF.captures(path) {
            return Some(format!(
                "codeforces.com/contest/{}/problem/{}",
                c.get(1).or(c.get(2))?.as_str(),
                c[3].to_ascii_uppercase()
            ));
        }
        if let Some(c) = GYM.captures(path) {
            return Some(format!(
                "codeforces.com/gym/{}/problem/{}",
                &c[1],
                c[2].to_ascii_uppercase()
            ));
        }
    }
    if host == "atcoder.jp" && AT.is_match(path) {
        return Some(format!("atcoder.jp{}", path.to_lowercase()));
    }
    if host == "luogu.com.cn" {
        if let Some(c) = LG.captures(path) {
            return Some(format!(
                "luogu.com.cn/problem/{}",
                c[1].to_ascii_uppercase()
            ));
        }
    }
    if host == "ac.nowcoder.com" {
        if let Some(c) = NC.captures(path) {
            return Some(format!(
                "ac.nowcoder.com/acm/contest/{}/{}",
                &c[1],
                c[2].to_ascii_uppercase()
            ));
        }
    }
    if host == "qoj.ac" {
        if let Some(c) = QOJ.captures(path) {
            return Some(format!("qoj.ac/problem/{}", &c[1]));
        }
    }
    let query = |name: &str| {
        parsed
            .query_pairs()
            .find(|(key, value)| key == name && !value.is_empty())
            .map(|(_, value)| value.into_owned())
    };
    for (hosts, target, parameter, prefix) in [
        (
            &["onlinejudge.org", "uva.onlinejudge.org"][..],
            "/index.php",
            "problem",
            "onlinejudge.org/problem/",
        ),
        (
            &["acm.hdu.edu.cn"][..],
            "/showproblem.php",
            "pid",
            "acm.hdu.edu.cn/problem/",
        ),
        (&["poj.org"][..], "/problem", "id", "poj.org/problem/"),
    ] {
        if hosts.contains(&host) && path == target {
            if let Some(id) = query(parameter)
                .filter(|value| !value.is_empty() && value.chars().all(|c| c.is_ascii_digit()))
            {
                return Some(format!("{prefix}{id}"));
            }
        }
    }
    if host == "spoj.com" && SPOJ.is_match(path) {
        return Some(format!(
            "spoj.com{}",
            path.to_ascii_uppercase()
                .replace("/PROBLEMS/", "/problems/")
        ));
    }
    if ["http", "https"].contains(&parsed.scheme()) {
        Some(format!("{host}{path}"))
    } else {
        None
    }
}
