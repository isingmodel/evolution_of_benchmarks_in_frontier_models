#!/usr/bin/env python3
"""Small client for the local openai-oauth Responses proxy.

The project intentionally talks to a localhost proxy instead of importing an
LLM vendor SDK. By default it uses the sibling checkout at ~/dev/openai-oauth,
while also accepting the underscore path requested in older notes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlparse


DEFAULT_OPENAI_OAUTH_BASE_URL = "http://127.0.0.1:10531/v1"
DEFAULT_OPENAI_OAUTH_MODEL = "gpt-5.4-mini"


def resolve_openai_oauth_dir(raw_path: str | Path | None = None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser()

    env_path = os.environ.get("OPENAI_OAUTH_DIR", "").strip()
    candidates = [
        Path(env_path).expanduser() if env_path else None,
        Path("~/dev/openai-oauth").expanduser(),
        Path("~/dev/openai_oauth").expanduser(),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return Path("~/dev/openai-oauth").expanduser()


def extract_response_text(payload: Mapping[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in payload.get("output", []) if isinstance(payload.get("output"), list) else []:
        if not isinstance(item, Mapping):
            continue
        content = item.get("content", [])
        if isinstance(content, Mapping):
            content = [content]
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, Mapping):
                continue
            block_type = block.get("type")
            text = block.get("text")
            if block_type in {"output_text", "text"} and isinstance(text, str):
                chunks.append(text)

    if chunks:
        return "\n".join(chunk for chunk in chunks if chunk.strip()).strip()

    choices = payload.get("choices", [])
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, Mapping):
                continue
            message = choice.get("message", {})
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                chunks.append(message["content"])
    return "\n".join(chunk for chunk in chunks if chunk.strip()).strip()


class OpenAIOAuthClient:
    def __init__(
        self,
        base_url: str = DEFAULT_OPENAI_OAUTH_BASE_URL,
        model: str = DEFAULT_OPENAI_OAUTH_MODEL,
        project_dir: str | Path | None = None,
        auto_start: bool = True,
        timeout: float = 120.0,
        start_timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.project_dir = resolve_openai_oauth_dir(project_dir)
        self.auto_start = auto_start
        self.timeout = timeout
        self.start_timeout = start_timeout
        self._process: Optional[subprocess.Popen[str]] = None

    def __enter__(self) -> "OpenAIOAuthClient":
        self.ensure_server()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        if not self._process:
            return
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def ensure_server(self) -> None:
        if self._server_ready():
            return
        if not self.auto_start:
            raise RuntimeError(
                f"OpenAI OAuth proxy is not reachable at {self.base_url}. "
                "Start openai-oauth or remove --no-openai-oauth-start."
            )

        command = self._start_command()
        self.close()
        self._process = subprocess.Popen(
            command,
            cwd=str(self.project_dir) if self.project_dir.exists() else None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        deadline = time.time() + self.start_timeout
        while time.time() < deadline:
            if self._process.poll() is not None:
                returncode = self._process.returncode
                self.close()
                raise RuntimeError(f"openai-oauth exited early with code {returncode}")
            if self._server_ready():
                return
            time.sleep(0.5)
        self.close()
        raise RuntimeError(f"Timed out waiting for openai-oauth at {self.base_url}")

    def generate_text(self, prompt: str, model: str | None = None) -> str:
        self.ensure_server()
        try:
            import requests
        except ImportError as e:
            raise RuntimeError("OpenAI OAuth client requires requests.") from e

        payload = {
            "model": model or self.model,
            "stream": False,
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }
            ],
        }
        response = requests.post(f"{self.base_url}/responses", json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI OAuth request failed {response.status_code}: {response.text[:500]}")
        try:
            body = response.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(f"OpenAI OAuth returned non-JSON response: {response.text[:500]}") from e
        text = extract_response_text(body)
        if not text:
            raise RuntimeError("OpenAI OAuth response did not contain output text.")
        return text

    def _server_ready(self) -> bool:
        try:
            import requests
        except ImportError:
            return False
        try:
            response = requests.get(f"{self.base_url}/models", timeout=2)
            return 200 <= response.status_code < 300
        except requests.RequestException:
            return False

    def _start_command(self) -> list[str]:
        parsed = urlparse(self.base_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 10531
        cli_source = self.project_dir / "packages" / "openai-oauth" / "src" / "cli.ts"
        bun = shutil.which("bun")
        if cli_source.exists() and bun:
            return [
                bun,
                "packages/openai-oauth/src/cli.ts",
                "--host",
                host,
                "--port",
                str(port),
                "--models",
                self.model,
            ]
        return [
            "npx",
            "--yes",
            "openai-oauth",
            "--host",
            host,
            "--port",
            str(port),
            "--models",
            self.model,
        ]
