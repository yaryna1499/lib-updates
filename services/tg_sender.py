import logging
import aiohttp
import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    @staticmethod
    async def send(session: aiohttp.ClientSession, text: str) -> None:
        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
        async with session.post(
            url, json={"chat_id": settings.CHAT_ID, "text": text, "parse_mode": "HTML"}
        ) as resp:
            if not resp.ok:
                body = await resp.text()
                logger.error("Telegram send failed: %s %s", resp.status, body)
                raise RuntimeError(f"Telegram API returned {resp.status}: {body}")
