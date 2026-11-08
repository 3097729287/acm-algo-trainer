//! ToBe domain services. This crate has no WebView, HTTP server or Python runtime.
pub mod ability;
pub mod api;
pub mod catalogue;
pub mod code_format;
pub mod contest_history;
pub mod custom_lists;
pub mod identity;
pub mod journal_export;
pub mod learning;
pub mod library;
pub mod migration;
pub mod native_judge;
pub mod planner;
pub mod preferences;
pub mod process_job;
pub mod public_assets;
pub mod reviews;
pub mod run_queue;
pub mod service;
pub mod storage;
pub mod templates;
pub mod training;
pub mod usage;

pub use api::{ApiError, ApiRequest, ApiResponse};
pub use service::{Service, ServiceConfig};
