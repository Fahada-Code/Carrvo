from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str
    carrvo_home: Path = Path("~/.carrvo").expanduser()
    latex_cmd: str = "pdflatex"
    browser_ws_endpoint: str = ""
    log_level: str = "INFO"
    # Comma-separated string (env: CORS_ORIGINS) so it can be set without JSON quoting.
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def jobs_dir(self) -> Path:
        return self.carrvo_home / "jobs"

    @property
    def resume_path(self) -> Path:
        return self.carrvo_home / "resume.tex"

    @property
    def cover_letter_path(self) -> Path:
        return self.carrvo_home / "coverletter.tex"

    @property
    def applications_log(self) -> Path:
        return self.carrvo_home / "applications.json"

    @property
    def qa_bank(self) -> Path:
        return self.carrvo_home / "qa_bank.json"


settings = Settings()  # type: ignore[call-arg]
