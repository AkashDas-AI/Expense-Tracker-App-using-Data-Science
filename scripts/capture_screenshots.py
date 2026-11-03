"""
Automated Streamlit Dashboard Screenshot Capture using Selenium

Author: Akash Das
Description: Captures pixel-perfect, fully rendered 1920x1080 screenshots of all
             6 primary Streamlit dashboard views in dark mode after all WebSocket
             streams, Plotly charts, and metric cards have settled.
"""

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "images"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
STREAMLIT_APP = PROJECT_ROOT / "app.py"
PORT = 8501

PAGES = [
    ("dashboard_overview.png", f"http://127.0.0.1:{PORT}/?page=overview"),
    ("spending_analysis.png", f"http://127.0.0.1:{PORT}/?page=spending"),
    ("budget_analysis.png", f"http://127.0.0.1:{PORT}/?page=budget"),
    ("financial_insights.png", f"http://127.0.0.1:{PORT}/?page=forecasting&tab=insights"),
    ("anomaly_detection.png", f"http://127.0.0.1:{PORT}/?page=forecasting&tab=anomalies"),
    ("expense_forecasting.png", f"http://127.0.0.1:{PORT}/?page=forecasting&tab=forecasting"),
]


def capture_all_screenshots() -> bool:
    """Launch Streamlit and capture screenshots with Selenium WebDriver."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    cmd = [
        str(VENV_PYTHON),
        "-m",
        "streamlit",
        "run",
        str(STREAMLIT_APP),
        f"--server.port={PORT}",
        "--server.headless=true",
        "--server.address=127.0.0.1",
        "--browser.serverAddress=127.0.0.1",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]

    print(f"Starting Streamlit server on 127.0.0.1:{PORT}...")
    proc = subprocess.Popen(cmd, env=env)

    driver = None
    try:
        # Wait for Streamlit server to be ready
        ready = False
        health_url = f"http://127.0.0.1:{PORT}/_stcore/health"
        for _ in range(30):
            time.sleep(1)
            try:
                with urllib.request.urlopen(health_url, timeout=2) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                pass

        if not ready:
            print("Streamlit server failed to start within 30 seconds.")
            return False

        print("Streamlit server is ready. Initializing Chrome WebDriver...")
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--hide-scrollbars")
        options.add_argument("--force-device-scale-factor=1")

        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1920, 1080)

        for filename, url in PAGES:
            out_file = IMAGES_DIR / filename
            print(f"Navigating to {url}...")
            driver.get(url)

            # Wait for main container and metrics/charts to render
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stMetricValue'], .js-plotly-plot, [data-testid='stMarkdownContainer']"))
                )
            except Exception as e:
                print(f"  Timeout waiting for content: {e}")

            # Additional pause for Plotly rendering and WebSocket settling
            time.sleep(3)

            # Save screenshot
            driver.save_screenshot(str(out_file))
            size_kb = out_file.stat().st_size / 1024
            print(f"  [OK] Saved {filename} ({size_kb:.1f} KB)")

        return True

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        print("Stopping Streamlit server...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Streamlit server stopped.")


if __name__ == "__main__":
    success = capture_all_screenshots()
    sys.exit(0 if success else 1)
