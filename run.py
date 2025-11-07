import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ensure_camoufox_browser():
    """Ensure Camoufox browser binary is downloaded."""
    # Try to locate the browser binary
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "camoufox", "path"],
            text=True, cwd=str(HERE)
        ).strip()
    except Exception:
        out = ""

    def looks_like_browser_dir(p: Path) -> bool:
        return p.exists() and p.is_dir()

    def find_exe_in(dir_path: Path) -> Path | None:
        exe_name = "camoufox.exe" if os.name == "nt" else "camoufox"
        for path in dir_path.rglob(exe_name):
            return path
        return None

    exe_path: Path | None = None
    if out:
        p = Path(out)
        if p.is_file():
            exe_path = p
        elif looks_like_browser_dir(p):
            exe_path = find_exe_in(p)

    if exe_path and exe_path.exists():
        print(f"[✓] Camoufox binary present at {exe_path}")
        return

    print("[!] Camoufox browser binary not found. Fetching…")
    subprocess.check_call(
        [sys.executable, "-m", "camoufox", "fetch"],
        cwd=str(HERE)
    )


def wait_for_server(url: str, timeout: int = 10) -> bool:
    """Wait for Flask server to be ready."""
    import urllib.request
    import urllib.error
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except urllib.error.URLError:
            time.sleep(0.5)
    return False


def launch_flask_server():
    """Start Flask server in background thread."""
    # Change to backend directory and start Flask
    backend_dir = HERE / "backend"
    
    def run_flask():
        os.chdir(str(backend_dir))
        # Import and run Flask app
        sys.path.insert(0, str(backend_dir))
        from app import app
        app.run(host='localhost', port=5000, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()
    print("[✓] Flask server starting...")


def open_browser(url: str):
    """Open default browser to the application URL."""
    webbrowser.open(url)
    print(f"[✓] Opened browser at {url}")


def main():
    print("[✓] Starting Camoufox Manager…\n")
    
    ensure_camoufox_browser()
    
    print("\n[✓] Environment ready. Launching application…\n")
    
    # Start Flask server
    launch_flask_server()
    
    # Wait for server to be ready
    url = 'http://localhost:5000'
    if wait_for_server(url):
        # Open browser
        open_browser(url)
        print("\n[✓] Application running. Press Ctrl+C to stop.\n")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[✓] Shutting down...")
            sys.exit(0)
    else:
        print("[!] Server failed to start within timeout")
        sys.exit(1)

if __name__ == "__main__":
    main()
