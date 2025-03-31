from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict

from services.app.schemas import TokenType


class DatabaseSettings(BaseSettings):
    DB_HOST: str = ""
    DB_PORT: int = 0
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASS: str = ""

    model_config = SettingsConfigDict(env_file=".env", frozen=True, env_ignore_empty=True)

    def get_db_url(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(env_file=".env", frozen=True, env_ignore_empty=True)

    @staticmethod
    def get_expiration(token_type: TokenType) -> timedelta:
        expires_deltas: dict[TokenType, timedelta] = {
            TokenType.ACCESS: timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            TokenType.REFRESH: timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        }
        return expires_deltas[token_type]


class RedisSettings(BaseSettings):
    REDIS_HOST: str = ""
    REDIS_PORT: int = 0
    REDIS_DB: int = 0
    REDIS_PASS: str = ""

    model_config = SettingsConfigDict(env_file=".env", frozen=True, env_ignore_empty=True)


class FrontendSettings(BaseSettings):
    MAIN_URL_HTTP: str = ""
    MAIN_URL_WS: str = ""

    model_config = SettingsConfigDict(env_file=".env", frozen=True, env_ignore_empty=True)


class Settings(
    DatabaseSettings,
    SecuritySettings,
    RedisSettings,
    FrontendSettings
):
    pass


settings = Settings()
