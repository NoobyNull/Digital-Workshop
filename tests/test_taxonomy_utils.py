from src.core.taxonomy_utils import split_category_and_keywords


def test_split_category_and_keywords_extracts_top_level_category() -> None:
    raw = ["Animals", "Cat", "Domestic"]

    category, keywords = split_category_and_keywords(raw)

    assert category == "Animals"
    assert keywords == ["Cat", "Domestic"]


def test_split_category_and_keywords_is_case_insensitive() -> None:
    raw = ["vehicles", "Sports Car", "Corvette"]

    category, keywords = split_category_and_keywords(raw)

    assert category == "Vehicles"
    assert keywords == ["Sports Car", "Corvette"]


def test_split_category_and_keywords_handles_no_category_match() -> None:
    raw = ["Wall Art", "Living Room"]

    category, keywords = split_category_and_keywords(raw)

    assert category is None
    assert keywords == ["Wall Art", "Living Room"]
