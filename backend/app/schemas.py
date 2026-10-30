"""The structured memory Gemma returns. Pydantic validates it before we store it."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Confidence = Literal["clear", "unclear"]


class Change(BaseModel):
    original: str
    corrected: str
    reason: str = ""


class PersonMention(BaseModel):
    name: str
    relationship_to_speaker: Optional[str] = None
    source_sentence: str
    confidence: Confidence = "unclear"
    grounded: Optional[bool] = None  # set by our check, not by Gemma


class PlaceMention(BaseModel):
    name: str
    source_sentence: str
    confidence: Confidence = "unclear"
    grounded: Optional[bool] = None


class TimePeriod(BaseModel):
    description: str
    source_sentence: str
    confidence: Confidence = "unclear"
    grounded: Optional[bool] = None


class Attribute(BaseModel):
    value: str
    source_sentence: str
    grounded: Optional[bool] = None


class Proverb(BaseModel):
    luganda: str
    english: str
    source_sentence: str
    grounded: Optional[bool] = None


class FollowUpQuestion(BaseModel):
    luganda: str
    english: str
    answered: bool = False


class StructuredMemory(BaseModel):
    title: str
    luganda_text: str
    english_text: str
    changes_made: list[Change] = Field(default_factory=list)
    people: list[PersonMention] = Field(default_factory=list)
    places: list[PlaceMention] = Field(default_factory=list)
    time_periods: list[TimePeriod] = Field(default_factory=list)
    clan: Optional[Attribute] = None
    totem: Optional[Attribute] = None
    proverbs: list[Proverb] = Field(default_factory=list)
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)


class TextPart(BaseModel):
    """First Gemma call: the story itself."""

    title: str
    luganda_text: str
    english_text: str
    changes_made: list[Change] = Field(default_factory=list)


class ExtractPart(BaseModel):
    """Second Gemma call: what the story mentions."""

    people: list[PersonMention] = Field(default_factory=list)
    places: list[PlaceMention] = Field(default_factory=list)
    time_periods: list[TimePeriod] = Field(default_factory=list)
    proverbs: list[Proverb] = Field(default_factory=list)
    clan: Optional[Attribute] = None
    totem: Optional[Attribute] = None
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)


def gemma_json_schema(model: type[BaseModel] = StructuredMemory) -> dict:
    """Schema sent to Ollama's structured-output `format`, without our own bookkeeping fields."""
    schema = model.model_json_schema()
    for d in [schema, *schema.get("$defs", {}).values()]:
        props = d.get("properties", {})
        props.pop("grounded", None)
        props.pop("answered", None)
        d["required"] = list(props)  # make Gemma write every field, even if only [] or null
    return schema
