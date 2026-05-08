from pydantic import BaseModel, Field


class DeckAnalyzeRequest(BaseModel):
    name: str = Field(..., description="Display name for the deck")
    format: str = Field(default="commander", description="Deck format")
    commander: str | None = Field(default=None, description="Commander name for commander decks")
    decklist: str = Field(..., description="Raw main decklist text")
    sideboard: str | None = Field(default=None, description="Optional sideboard list for supported formats")
