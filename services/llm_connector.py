import logging


from openai import AsyncOpenAI
import settings
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a changelog analyzer.

You receive raw changelog text that may contain Markdown formatting (headings, links, bold text, code, bullet points). Treat ALL formatting as noise.

Your task:
- Ignore Markdown syntax completely (do not interpret it as structure)
- Focus only on the actual meaning of the text

Then:
- Identify the most important changes for users (new features, important fixes, security fixes, breaking changes)
- Ignore minor updates, dependency bumps, internal refactoring unless user-impacting

Output requirements:
- Ukrainian language only
- 3 sentences maximum
- No Markdown in output
- No bullet points
- No links unless absolutely critical to understanding a change
- Do not repeat version numbers unless relevant to meaning
- Do not mirror input structure
- Output ONLY the final summary text

If changes are minor or mostly dependency updates, say that the release contains mainly maintenance updates and minor improvements."""

class LLMConnector:
    def __init__(self) -> None:
        assert settings.OPENROUTER_API_KEY is not None, "OPENROUTER_API_KEY must be set"
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )

    async def llm_summarize(self, summary: str) -> str:
        assert settings.MODEL is not None, "MODEL must be set"
        response = await self.client.chat.completions.create(
            model=settings.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {"role": "user", "content": summary},
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            return "No summary available."
        logger.info("LLM summary: %s", content[:120].replace("\n", " "))
        return content


llm_connector: LLMConnector = LLMConnector()
