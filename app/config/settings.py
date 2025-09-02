from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    shouldBuffer: bool = Field(default=False, alias="BUFFER_OPERATIONS")

    bufferSeconds: int = Field(default=10, alias="BUFFER_TIME_SEC")

    backoffMin: int = Field(default=10, alias="RATE_LIMIT_BACKOFF_MIN")

    shouldRetry: bool = Field(default=True, alias="SHOULD_RETRY")

    maxRetries: int = Field(default=3, alias="MAX_RETRIES")

    usePacificTz: bool = Field(default=True, alias="DATETIME_USE_PACIFIC")

    caseSensitiveVaultNames: bool = Field(
        default=False, alias="CASE_SENSITIVE_VAULT_NAMES"
    )

    vaultNameJoiner: str = Field(default=".")


settings = Settings()
