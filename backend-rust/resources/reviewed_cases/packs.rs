// Generated fixed public identities; never match a title or tags.
fn packed_bytes(identity: &str) -> Option<&'static [u8]> {
    match identity {
        "ABC 478::D" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-00.json.gz"))),
        "ABC 478::E" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-01.json.gz"))),
        "Div.4 1003::C1" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-02.json.gz"))),
        "Div.4 1003::C2" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-03.json.gz"))),
        "Div.4 1003::D" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-04.json.gz"))),
        "Div.4 1003::G" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-05.json.gz"))),
        "Div.4 993::E" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-06.json.gz"))),
        "Div.4 993::H" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-07.json.gz"))),
        "入门赛 46::H" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-08.json.gz"))),
        "入门赛 49::D" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-09.json.gz"))),
        "入门赛 50::F" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-10.json.gz"))),
        "周赛 164::C" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-11.json.gz"))),
        "周赛 164::D" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-12.json.gz"))),
        "周赛 164::F" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-13.json.gz"))),
        "基础赛 37::B" => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/profile-14.json.gz"))),
        _ => None,
    }
}
