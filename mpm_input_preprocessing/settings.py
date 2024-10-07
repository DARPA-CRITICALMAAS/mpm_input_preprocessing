from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        env_prefix="mpm_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    cdr_bearer_token: str = "Bearer a0d45e47f4884fa5c3f9d13154a6ddf389373c184f224a1d4dbe88ed2e96b1512"

    cdr_s3_endpoint_url: str = "http://172.17.0.1:9000"  # "https://s3.amazonaws.com"
    cdr_public_bucket: str = "public.cdr.land"
    cdr_endpoint_url: str = "http://172.17.0.1:8333"

    api_prefix: str ="/v1"

    registration_secret: str = "test"

    SYSTEM: str = "mpm_input_preprocessing"
    SYSTEM_VERSION: str = "0.0.1"
    

app_settings = Settings()
