from app.grounding import ground
from app.schemas import StructuredMemory

TRANSCRIPT = (
    "Nze Nalongo Namubiru. Nazaalibwa mu Masaka mu mwaka gwa 1948. "
    "Taata wange yali ayitibwa Kizito, era yali mulimi wa mmwanyi."
)


def memory(**extra):
    base = {"title": "t", "luganda_text": TRANSCRIPT, "english_text": "e"}
    return StructuredMemory.model_validate({**base, **extra})


def test_real_person_is_grounded_and_quote_is_exact():
    m, _ = ground(memory(people=[{"name": "Kizito", "relationship_to_speaker": "father",
        "source_sentence": "taata wange yali ayitibwa kizito era yali mulimi wa mmwanyi", "confidence": "clear"}]), TRANSCRIPT)
    assert m.people[0].grounded is True
    assert m.people[0].source_sentence == "Taata wange yali ayitibwa Kizito, era yali mulimi wa mmwanyi."


def test_invented_person_is_flagged_unclear():
    m, notes = ground(memory(people=[{"name": "Mukasa", "relationship_to_speaker": "uncle",
        "source_sentence": "Kojja wange Mukasa yali mulungi.", "confidence": "clear"}]), TRANSCRIPT)
    assert m.people[0].grounded is False
    assert m.people[0].confidence == "unclear"
    assert notes


def test_name_not_in_a_real_sentence_is_flagged():
    m, _ = ground(memory(people=[{"name": "Mukasa", "relationship_to_speaker": None,
        "source_sentence": "Nazaalibwa mu Masaka mu mwaka gwa 1948.", "confidence": "clear"}]), TRANSCRIPT)
    assert m.people[0].grounded is False


def test_guessed_clan_is_removed():
    m, notes = ground(memory(clan={"value": "Ngeye", "source_sentence": "Ndi wa kika kya Ngeye."}), TRANSCRIPT)
    assert m.clan is None
    assert any("clan" in n for n in notes)


def test_unclear_clan_value_is_dropped():
    m, _ = ground(memory(totem={"value": "unclear", "source_sentence": ""}), TRANSCRIPT)
    assert m.totem is None


def test_no_op_changes_are_dropped():
    m, _ = ground(memory(changes_made=[{"original": "Nze.", "corrected": "Nze.", "reason": "none"},
                                       {"original": "mmwanyi", "corrected": "mmwaanyi", "reason": "spelling"}]), TRANSCRIPT)
    assert [c.original for c in m.changes_made] == ["mmwanyi"]


def test_sentences_split_after_closing_quote():
    from app.grounding import split_sentences

    assert split_sentences('Taata yagamba nti, "Agali awamu." Mu biseera bya Amin twadduka.') == [
        'Taata yagamba nti, "Agali awamu."',
        "Mu biseera bya Amin twadduka.",
    ]


def test_photo_description_loses_sentences_with_names():
    from app.grounding import remove_names

    text, notes = remove_names("Two women stand by a house. The older one is Nakato Namubiru. It is a faded photo.", ["Nakato"])
    assert text == "Two women stand by a house. It is a faded photo."
    assert len(notes) == 1 and "nakato" in notes[0]


def test_photo_description_keeps_ordinary_words_that_are_also_names():
    from app.grounding import remove_names

    text, notes = remove_names("A faded photo of a woman holding a rose.", ["Rose Nalwoga", "Photo Test"])
    assert text == "A faded photo of a woman holding a rose." and notes == []


def test_looping_luganda_and_repeated_questions_are_cleaned():
    from app.grounding import clean_questions

    qs = [
        {"luganda": "Jjajja, oba nnyo nnyo nnyo nnyo", "english": "Who is this?"},
        {"luganda": "Jjajja, ani ono?", "english": "Who is this?"},
        {"luganda": "Jjajja, kino kyakubibwa ddi?", "english": "When was this taken?"},
    ]
    kept, notes = clean_questions(qs)
    assert [q["english"] for q in kept] == ["Who is this?", "When was this taken?"]
    assert kept[0]["luganda"] == "" and len(notes) == 1
    assert kept[1]["luganda"] == "Jjajja, kino kyakubibwa ddi?"
