from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://procure:procure@localhost:5432/procureai"
    OPENAI_API_KEY: str = "local"           # llama.cpp ignores this, but client requires a non-empty value
    LLM_BASE_URL: str = ""                  # empty = use OpenAI cloud; set to e.g. http://127.0.0.1:8082/v1
    LLM_MODEL: str = "gpt-4o-mini"         # model name sent to the server

    model_config = {"env_file": ".env"}


settings = Settings()
