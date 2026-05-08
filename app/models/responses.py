from pydantic import BaseModel, Field


class CardDetails(BaseModel):
    name: str
    mana_cost: str | None = None
    mana_value: float | int | None = None
    type_line: str | None = None
    oracle_text: str | None = None
    colors: list[str] = Field(default_factory=list)
    color_identity: list[str] = Field(default_factory=list)
    image_small: str | None = None
    image_normal: str | None = None
    scryfall_uri: str | None = None


class CommanderSummary(BaseModel):
    name: str
    color_identity: list[str] = Field(default_factory=list)
    type_line: str | None = None
    image_small: str | None = None
    scryfall_uri: str | None = None


class DeckCardEntry(BaseModel):
    quantity: int
    name: str
    categories: list[str] = Field(default_factory=list)
    card: CardDetails | None = None


class ArchetypeGuess(BaseModel):
    name: str
    confidence: float
    reasons: list[str] = Field(default_factory=list)
    support_cards: list[str] = Field(default_factory=list)


class DeckAnalyzeResponse(BaseModel):
    deck_name: str
    format: str
    commander: CommanderSummary | None = None
    commanders: list[CommanderSummary] = Field(default_factory=list)
    deck_color_identity: list[str] = Field(default_factory=list)
    color_identity_violations: list[str] = Field(default_factory=list)
    total_cards: int
    mainboard_count: int = 0
    sideboard_count: int = 0
    unique_cards: int
    color_identity: list[str] = Field(default_factory=list)
    mana_curve: dict[str, int] = Field(default_factory=dict)
    type_breakdown: dict[str, int] = Field(default_factory=dict)
    classification_counts: dict[str, int] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    primary_archetype: str | None = None
    archetype_guesses: list[ArchetypeGuess] = Field(default_factory=list)
    parsed_cards: list[DeckCardEntry] = Field(default_factory=list)
    parsed_sideboard: list[DeckCardEntry] = Field(default_factory=list)
