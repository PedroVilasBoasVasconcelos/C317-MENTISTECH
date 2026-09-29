import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8765"


def wait_for_server(process: subprocess.Popen, timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("O servidor FastAPI encerrou antes dos testes iniciarem.")

        try:
            with urllib.request.urlopen(BASE_URL, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)

    raise RuntimeError("O servidor FastAPI não ficou disponível a tempo.")


@pytest.fixture(scope="session", autouse=True)
def app_server():
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_server(process)
        yield
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def authenticated_page(page):
    page.goto("/")
    page.evaluate(
        """
        localStorage.setItem("access_token", "e2e-token");
        localStorage.setItem("token_type", "bearer");
        localStorage.setItem("user_email", "ana@example.com");
        """
    )
    return page
