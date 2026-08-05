from mnemosyne.graph.nlp import extract_entities


def test_extract_entities():
    text = "Apple Inc. announced today that Steve Jobs visited Cupertino."
    entities = extract_entities(text)

    # We expect:
    # - Apple Inc. (ORG)
    # - today (DATE)
    # - Steve Jobs (PERSON)
    # - Cupertino (GPE -> LOCATION)

    assert len(entities) >= 4

    types = [e["type"] for e in entities]
    names = [e["name"] for e in entities]
    ids = [e["id"] for e in entities]

    assert "ORG" in types
    assert "Apple Inc." in names

    assert "PERSON" in types
    assert "Steve Jobs" in names
    assert "steve_jobs" in ids

    assert "LOCATION" in types
    assert "Cupertino" in names

    assert "DATE" in types
    assert "today" in names


def test_extract_entities_empty():
    assert extract_entities("   ") == []
    assert extract_entities("") == []
