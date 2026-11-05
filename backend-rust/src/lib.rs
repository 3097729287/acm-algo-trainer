//! ToBe domain services. This crate has no WebView, HTTP server or Python runtime.
pub mod api;
pub mod library;
pub mod migration;
pub mod service;
pub mod storage;
pub mod templates;

pub use api::{ApiError, ApiRequest, ApiResponse};
pub use service::{Service, ServiceConfig};
