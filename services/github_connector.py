import logging
from typing import Any
import aiohttp
import settings

logger = logging.getLogger(__name__)


class GithubConnector:
    @staticmethod
    async def fetch_latest(session: aiohttp.ClientSession, repo: str) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repo}/releases/latest"

        headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }

        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("GitHub error: %s %s %s", repo, resp.status, text)
                raise RuntimeError(f"GitHub API returned {resp.status} for {repo}: {text}")

            return await resp.json()
