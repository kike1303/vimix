use tauri::Manager;
use tauri_plugin_shell::ShellExt;

/// Holds the API port so the frontend can query it via IPC.
struct ApiPort(u16);

/// Tauri command: returns the sidecar API port to the frontend.
#[tauri::command]
fn get_api_port(state: tauri::State<ApiPort>) -> u16 {
    state.0
}

/// Find a free TCP port for the sidecar API.
fn find_free_port() -> u16 {
    portpicker::pick_unused_port().expect("No free port available")
}

/// Start the Python sidecar on the given port.
///
/// Resolves bundled ffmpeg/ffprobe/img2webp paths from Tauri resources
/// and passes them to the sidecar via environment variables so the
/// Python `binary_paths` module can find them.
fn spawn_sidecar(app: &tauri::AppHandle, port: u16) {
    // Resolve resource directory to find bundled binaries
    let resource_dir = app
        .path()
        .resource_dir()
        .expect("Failed to resolve resource directory");

    let ext = if cfg!(windows) { ".exe" } else { "" };
    let ffmpeg_path = resource_dir.join("resources").join(format!("ffmpeg{ext}"));
    let ffprobe_path = resource_dir.join("resources").join(format!("ffprobe{ext}"));
    let img2webp_path = resource_dir.join("resources").join(format!("img2webp{ext}"));

    // Set env vars so the Python sidecar can find the bundled binaries
    std::env::set_var("FFMPEG_BIN", &ffmpeg_path);
    std::env::set_var("FFPROBE_BIN", &ffprobe_path);
    std::env::set_var("IMG2WEBP_BIN", &img2webp_path);

    let shell = app.shell();
    let sidecar = shell
        .sidecar("Vimix-processor")
        .expect("Failed to locate sidecar binary")
        .args(["--port", &port.to_string()]);

    let (mut _rx, child) = sidecar.spawn().expect("Failed to spawn sidecar");

    // Keep the child handle alive for the app's lifetime.
    // Tauri automatically kills child processes on app exit.
    Box::leak(Box::new(child));
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let port = find_free_port();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .manage(ApiPort(port))
        .setup(move |app| {
            // Start the Python backend sidecar
            spawn_sidecar(app.handle(), port);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_api_port])
        .run(tauri::generate_context!())
        .expect("error while running Vimix");
}
