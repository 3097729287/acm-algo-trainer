//! ToBe domain services. This crate has no WebView, HTTP server or Python runtime.
pub mod api;
pub mod catalogue;
pub mod code_format;
pub mod learning;
pub mod library;
pub mod migration;
pub mod planner;
pub mod preferences;
pub mod service;
pub mod storage;
pub mod templates;
pub mod training;
pub mod usage;

pub use api::{ApiError, ApiRequest, ApiResponse};
pub use service::{Service, ServiceConfig};
