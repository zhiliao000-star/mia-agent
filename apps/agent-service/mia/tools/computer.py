import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from langchain_core.tools import StructuredTool

from mia.integrations.convex import ConvexClient


KNOWN_SITES = {
    "wikipedia": "https://www.wikipedia.org",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
}


def resolve_url(target: str) -> str:
    cleaned = target.strip()
    lowered = cleaned.lower()
    for name, url in KNOWN_SITES.items():
        if name in lowered:
            return url

    match = re.search(r"https?://[^\s]+", cleaned)
    if match:
        url = match.group(0).rstrip(".,)")
    else:
        domain = lowered.strip(" .")
        if not domain:
            raise ValueError("No URL or known website was provided")
        url = f"https://{domain}"

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only http and https URLs are allowed")
    return url


def _pending_reply(code: str, summary: str) -> str:
    return f"Approval needed: {summary}\nReply approve to run it."


def build_computer_tools(
    convex: ConvexClient | None = None,
    *,
    requester_number: str = "",
    message_handle: str = "",
    run_id: str | None = None,
) -> list[StructuredTool]:
    async def open_url(target: str) -> str:
        url = resolve_url(target)
        subprocess.run(["open", url], check=True)
        return f"Opened {url}"

    async def read_file(path: str) -> str:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists() or not file_path.is_file():
            return f"File not found: {file_path}"
        content = file_path.read_text(errors="replace")
        return content[:12000]

    async def request_terminal_command(command: str, cwd: str = "") -> str:
        if convex is None:
            return "Approval backend is unavailable."
        summary = f"Run terminal command: {command}"
        code = await convex.create_pending_action(
            requester_number=requester_number,
            message_handle=message_handle,
            run_id=run_id,
            kind="run_terminal_command",
            summary=summary,
            payload={"command": command, "cwd": cwd},
            risk="approval_required",
        )
        return _pending_reply(code, summary)

    async def request_write_file(path: str, content: str) -> str:
        if convex is None:
            return "Approval backend is unavailable."
        summary = f"Write file: {path}"
        code = await convex.create_pending_action(
            requester_number=requester_number,
            message_handle=message_handle,
            run_id=run_id,
            kind="write_file",
            summary=summary,
            payload={"path": path, "content": content},
            risk="approval_required",
        )
        return _pending_reply(code, summary)

    async def request_delete_file(path: str) -> str:
        if convex is None:
            return "Approval backend is unavailable."
        summary = f"Delete file: {path}"
        code = await convex.create_pending_action(
            requester_number=requester_number,
            message_handle=message_handle,
            run_id=run_id,
            kind="delete_file",
            summary=summary,
            payload={"path": path},
            risk="approval_required",
        )
        return _pending_reply(code, summary)

    async def request_open_app(app_name: str) -> str:
        if convex is None:
            return "Approval backend is unavailable."
        summary = f"Open application: {app_name}"
        code = await convex.create_pending_action(
            requester_number=requester_number,
            message_handle=message_handle,
            run_id=run_id,
            kind="open_app",
            summary=summary,
            payload={"app_name": app_name},
            risk="approval_required",
        )
        return _pending_reply(code, summary)

    return [
        StructuredTool.from_function(
            coroutine=open_url,
            name="open_url",
            description="Open a safe http or https URL in the user's default browser on this Mac.",
        ),
        StructuredTool.from_function(
            coroutine=read_file,
            name="read_file",
            description="Read a local text file. Use only when the user asks to inspect a file.",
        ),
        StructuredTool.from_function(
            coroutine=request_terminal_command,
            name="run_terminal_command",
            description="Request approval to run a terminal command on this Mac.",
        ),
        StructuredTool.from_function(
            coroutine=request_write_file,
            name="write_file",
            description="Request approval to write a local file.",
        ),
        StructuredTool.from_function(
            coroutine=request_delete_file,
            name="delete_file",
            description="Request approval to delete a local file.",
        ),
        StructuredTool.from_function(
            coroutine=request_open_app,
            name="open_app",
            description="Request approval to open a local macOS application.",
        ),
    ]


def execute_pending_action(action: dict[str, Any]) -> str:
    kind = action["kind"]
    payload = action["payload"]
    if kind == "run_terminal_command":
        cwd = payload.get("cwd") or None
        completed = subprocess.run(
            payload["command"],
            cwd=cwd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=120,
        )
        output = "\n".join(
            part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
        )
        return f"exit={completed.returncode}\n{output}"[:12000]
    if kind == "write_file":
        path = Path(payload["path"]).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload["content"])
        return f"Wrote {path}"
    if kind == "delete_file":
        path = Path(payload["path"]).expanduser().resolve()
        if path.exists() and path.is_file():
            path.unlink()
            return f"Deleted {path}"
        return f"File not found: {path}"
    if kind == "open_app":
        subprocess.run(["open", "-a", payload["app_name"]], check=True)
        return f"Opened {payload['app_name']}"
    raise ValueError(f"Unsupported pending action kind: {kind}")
