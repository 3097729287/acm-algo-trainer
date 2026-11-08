#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Arc;
use tauri::{Manager, State};
use tobe_core::{ApiError, ApiRequest, ApiResponse, Service, ServiceConfig};

struct AppState(Arc<Service>);

#[tauri::command]
async fn api_request(
    window: tauri::WebviewWindow,
    state: State<'_, AppState>,
    request: ApiRequest,
) -> Result<ApiResponse, ApiError> {
    // Remote judge/login WebViews never get the local workspace's authority.
    if window.label() != "main" {
        return Err(ApiError::new(
            403,
            "WINDOW_SCOPE",
            "请求窗口无权访问本机数据",
        ));
    }
    let service = Arc::clone(&state.0);
    // SQLite/JSON and future bounded native jobs must never block WebView's UI
    // thread. Rust domain code is shared unchanged with the verification CLI.
    tauri::async_runtime::spawn_blocking(move || service.handle(request))
        .await
        .map_err(|_| ApiError::new(500, "COMMAND_FAILED", "本次操作未完成，本机数据已保留"))
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let source = std::env::var_os("TB_NATIVE_SOURCE_ROOT")
                .map(std::path::PathBuf::from)
                .unwrap_or(app.path().resource_dir()?);
            // Candidate state is isolated by application identifier and path.
            // Neither the current installation nor its login credentials are opened.
            let state = std::env::var_os("TB_NATIVE_SANDBOX_DIR")
                .map(std::path::PathBuf::from)
                .unwrap_or(source.join("state/native-migration-sandbox"));
            let config = ServiceConfig::sandbox(source, state.clone());
            let service = Service::open(config).map_err(|e| std::io::Error::other(e.message))?;
            let window = tauri::WebviewWindowBuilder::new(
                app,
                "main",
                tauri::WebviewUrl::App("index.html#native-check".into()),
            )
            .title("ToBe · Rust 迁移验证")
            .inner_size(1280., 820.)
            .min_inner_size(760., 560.)
            .data_directory(state.join("webview"))
            .visible(false)
            .on_navigation(|url| {
                url.scheme() == "tauri"
                    || url.host_str() == Some("tauri.localhost")
                    || cfg!(debug_assertions)
                        && matches!(url.host_str(), Some("localhost" | "127.0.0.1"))
            })
            .build()?;
            let fullscreen_window = window.clone();
            let service = service.with_desktop_fullscreen(move |requested| {
                let unavailable =
                    |_| ApiError::new(503, "DESKTOP_UNAVAILABLE", "原生窗口暂时不可用，请稍后重试");
                if let Some(fullscreen) = requested {
                    fullscreen_window
                        .set_fullscreen(fullscreen)
                        .map_err(unavailable)?;
                }
                fullscreen_window.is_fullscreen().map_err(unavailable)
            });
            app.manage(AppState(Arc::new(service)));
            window.show()?;
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![api_request])
        .run(tauri::generate_context!())
        .expect("ToBe native runtime failed");
}
