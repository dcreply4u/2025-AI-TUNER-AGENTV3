from __future__ import annotations

import argparse
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

import requests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = REPO_ROOT / "docs" / "chat_exports"


@dataclass
class ExportConfig:
    api_base: str
    api_key: str
    export_dir: Path
    repo_path: Path
    limit: int
    push: bool


def fetch_sessions(cfg: ExportConfig) -> Sequence[Mapping]:
    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    resp = requests.get(f"{cfg.api_base}/sessions", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def export_session(cfg: ExportConfig, session: Mapping) -> Path:
    session_id = session["id"]
    title = session.get("title") or f"session_{session_id}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = cfg.export_dir / f"{title}_{timestamp}.md"

    headers = {"Authorization": f"Bearer {cfg.api_key}"}
    chat_resp = requests.get(
        f"{cfg.api_base}/sessions/{session_id}", headers=headers, timeout=30
    )
    chat_resp.raise_for_status()
    chat = chat_resp.json()

    cfg.export_dir.mkdir(parents=True, exist_ok=True)
    with filename.open("w", encoding="utf-8") as handle:
        handle.write(f"# ChatNow Session: {title}\n\n")
        for message in chat.get("messages", []):
            sender = message.get("role", "unknown").capitalize()
            content = message.get("content", "").strip()
            handle.write(f"**{sender}:** {content}\n\n")
    LOGGER.info("Exported %s", filename)
    return filename


def git_commit_and_push(cfg: ExportConfig, files: Iterable[Path]) -> None:
    files = list(files)
    if not files:
        return
    subprocess.run(["git", "add", *map(str, files)], cwd=cfg.repo_path, check=True)
    message = f"Add ChatNow exports ({datetime.now():%Y-%m-%d})"
    subprocess.run(["git", "commit", "-m", message], cwd=cfg.repo_path, check=True)
    if cfg.push:
        subprocess.run(["git", "push"], cwd=cfg.repo_path, check=True)
        LOGGER.info("Pushed %d exports to remote", len(files))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ChatNow sessions to Markdown.")
    parser.add_argument("--limit", type=int, default=5, help="Number of sessions to export.")
    parser.add_argument("--api-base", default=os.getenv("CHATNOW_API_BASE", "https://api.chatnow.ai/v1"))
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--repo", type=Path, default=REPO_ROOT)
    parser.add_argument("--no-push", action="store_true", help="Skip git push step.")
    args = parser.parse_args()

    api_key = os.getenv("CHATNOW_API_KEY")
    if not api_key:
        raise SystemExit("CHATNOW_API_KEY environment variable is required.")

    cfg = ExportConfig(
        api_base=args.api_base.rstrip("/"),
        api_key=api_key,
        export_dir=args.export_dir,
        repo_path=args.repo,
        limit=args.limit,
        push=not args.no_push,
    )

    sessions = fetch_sessions(cfg)[: cfg.limit]
    exported: List[Path] = []
    for session in sessions:
        exported.append(export_session(cfg, session))
    git_commit_and_push(cfg, exported)


if __name__ == "__main__":
    main()

