from typing import Final
from dotenv import load_dotenv
import os

load_dotenv()

GH_TOKEN: Final[str | None] = os.getenv("GH_TOKEN")
BOT_TOKEN: Final[str | None] = os.getenv("BOT_TOKEN")
CHAT_ID: Final[str | None] = os.getenv("CHAT_ID")
OPENROUTER_API_KEY: Final[str | None] = os.getenv("OPENROUTER_API_KEY")
MODEL: Final[str | None] = os.getenv("MODEL")
