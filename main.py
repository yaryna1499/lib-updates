import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp
import aioschedule

from services.github_connector import GithubConnector
from services.tg_sender import TelegramBot
from services.llm_connector import llm_connector

logger = logging.getLogger(__name__)


# ---------- CONFIG ----------


@dataclass
class Config:
    repos: list[str] = field(
        default_factory=lambda: [
            "pydantic/pydantic",
            "fastapi/fastapi",
            "sqlalchemy/sqlalchemy",
            "astral-sh/uv",
            "sqlalchemy/alembic",
            "aio-libs/aiobotocore",
            "pytest-dev/pytest",
        ]
    )
    state_file: str = "state.json"
    check_interval_minutes: int = 30


# ---------- STATE ----------


class StateStore:
    """Persistent store of the latest seen tag per repo."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._data = self._load()

    def is_new(self, repo: str, tag: str) -> bool:
        return self._data.get(repo) != tag

    def mark_seen(self, repo: str, tag: str) -> None:
        self._data[repo] = tag
        self._save()

    def _load(self) -> dict[str, Any]:
        try:
            with open(self._path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("State file %s not found, starting fresh", self._path)
            return {}
        except json.JSONDecodeError:
            logger.warning("Corrupt state file %s, starting fresh", self._path)
            return {}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)


# ---------- MESSAGE ----------


def format_release_message(repo: str, tag: str, summary: str, html_url: str) -> str:
    return f"""🚀 <b>{repo}</b> <code>{tag}</code>

{summary}

🔗 {html_url}"""


# ---------- CHECKER ----------


async def check_releases(
    session: aiohttp.ClientSession,
    state: StateStore,
    config: Config,
) -> None:
    logger.info("Checking releases...")
    new_count = 0
    for repo in config.repos:
        try:
            data = await GithubConnector.fetch_latest(session, repo)

            tag = data["tag_name"]

            if not state.is_new(repo, tag):
                continue

            new_count += 1

            logger.info("New release: %s %s", repo, tag)

            body = data.get("body")
            if body:
                summary = await llm_connector.llm_summarize(body)
            else:
                summary = "No description provided."

            message = format_release_message(
                repo,
                tag,
                summary.strip(),
                data.get("html_url", ""),
            )
            await TelegramBot.send(session, message)

            state.mark_seen(repo, tag)

        except Exception:
            logger.exception("Failed to process %s", repo)

    logger.info("Finished checking %d repos (%d new)", len(config.repos), new_count)


# ---------- MAIN ----------


async def run() -> None:
    config = Config()
    state = StateStore(config.state_file)

    async with aiohttp.ClientSession() as session:
        aioschedule.every(config.check_interval_minutes).minutes.do(
            check_releases,
            session,
            state,
            config,
        )
        await check_releases(session, state, config)

        while True:
            await aioschedule.run_pending()
            await asyncio.sleep(max(0, aioschedule.idle_seconds()))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(run())
