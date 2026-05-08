from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "MTG Deck Analyzer API"
    version: str = "0.1.0"
    scryfall_base_url: str = "https://api.scryfall.com"
    scryfall_cache_ttl_seconds: int = 3600
    analyze_rate_limit_requests: int = 20
    analyze_rate_limit_window_seconds: int = 60


settings = Settings()
