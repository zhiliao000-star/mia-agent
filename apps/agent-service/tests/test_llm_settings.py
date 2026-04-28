import pytest

from mia.settings import Settings


def test_llm_config_requires_openai_compatible_environment() -> None:
    settings = Settings(
        OPENAI_API_KEY="",
        OPENAI_BASE_URL="",
        MODEL_NAME="",
        CONVEX_SITE_URL="https://convex.test",
        MIA_INTERNAL_SECRET="secret",
    )

    with pytest.raises(RuntimeError) as error:
        settings.validate_llm()

    message = str(error.value)
    assert "OPENAI_API_KEY" in message
    assert "OPENAI_BASE_URL" in message
    assert "MODEL_NAME" in message


def test_llm_config_accepts_custom_openai_compatible_provider() -> None:
    settings = Settings(
        OPENAI_API_KEY="key",
        OPENAI_BASE_URL="https://llm.example.com/v1",
        MODEL_NAME="custom-model",
    )

    settings.validate_llm()
