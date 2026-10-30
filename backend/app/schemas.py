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


class PhotoQuestion(BaseModel):
    # English only. Asked for Luganda as well, E2B looped ("nnyo nnyo nnyo ...") or drifted into
    # Kinyarwanda, so the family writes the Luganda wording themselves.
    english: str


class PhotoPart(BaseModel):
    """What Gemma sees in an old family photo. It describes; the family says who is in it."""

    description: str
    questions: list[PhotoQuestion] = Field(default_factory=list)


# Hard limits so a small model cannot loop forever ("ekyera ekyera ekyera ..."). Ollama turns
# maxLength / maxItems into its decoding grammar, so these are enforced while Gemma writes.
MAX_ITEMS = {"people": 30, "places": 25, "time_periods": 20, "proverbs": 10, "follow_up_questions": 5, "changes_made": 40, "questions": 5}
SHORT_TEXT = 300  # names, sentences, questions


def _limit_strings(node, max_len: int) -> None:
    if isinstance(node, dict):
        if node.get("type") == "string":
            node.setdefault("maxLength", max_len)
        for v in node.values():
            _limit_strings(v, max_len)
    elif isinstance(node, list):
        for v in node:
            _limit_strings(v, max_len)


def gemma_json_schema(model: type[BaseModel] = StructuredMemory, transcript_chars: int = 4000) -> dict:
    """Schema sent to Ollama's structured-output `format`, without our own bookkeeping fields."""
    schema = model.model_json_schema()
    for d in [schema, *schema.get("$defs", {}).values()]:
        props = d.get("properties", {})
        props.pop("grounded", None)
        props.pop("answered", None)
        d["required"] = list(props)  # make Gemma write every field, even if only [] or null
    props = schema["properties"]
    for name, limit in MAX_ITEMS.items():
        if name in props:
            props[name]["maxItems"] = limit
    long_text = int(transcript_chars * 1.6) + 200  # the story itself, in Luganda or English
    for name in ("luganda_text", "english_text"):
        if name in props:
            props[name]["maxLength"] = long_text
    if "description" in props:  # a photo description: a short paragraph
        props["description"]["maxLength"] = 800
    if "title" in props:
        props["title"]["maxLength"] = 120
    _limit_strings(schema, SHORT_TEXT)
    return schema
