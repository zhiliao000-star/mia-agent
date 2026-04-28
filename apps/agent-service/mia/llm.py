from langchain_openai import ChatOpenAI

from mia.settings import Settings


def build_chat_model(settings: Settings, *, temperature: float = 0) -> ChatOpenAI:
    settings.validate_llm()
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.model_name,
        temperature=temperature,
    )
