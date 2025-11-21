from datetime import datetime, timedelta

from src.core.search_engine import SearchEngine, parse_search_query_language


def test_parse_search_query_language_understands_tags_inproject_and_lat() -> None:
    """Mini-language parsing should separate filters from free text and dedupe tags."""
    # Mixed free text + filters
    query, filters = parse_search_query_language(
        "lathe tag=recent tag!=Vehicle inProject LAT>=50"
    )
    assert query == "lathe"
    assert filters["tags_include"] == ["recent"]
    assert filters["tags_exclude"] == ["Vehicle"]
    assert filters["in_project"] is True
    assert filters["lat_days"] == 50

    # Only filters, no free text
    query2, filters2 = parse_search_query_language("   tag=dirty   ")
    assert query2 == ""
    assert filters2 == {"tags_include": ["dirty"]}

    # Connectors with only filter tokens should not leak into free text
    query3, filters3 = parse_search_query_language(
        "LAT>=10 AND tag!=foo AND !inProject"
    )
    assert query3 == ""
    assert filters3["tags_exclude"] == ["foo"]
    assert filters3["in_project"] is False
    assert filters3["lat_days"] == 10

    # Duplicated tags should be deduplicated case-insensitively
    query4, filters4 = parse_search_query_language("tag=Dirty tag=dirty tag=DIRTY")
    assert query4 == ""
    assert filters4["tags_include"] == ["Dirty"]


def test_search_engine_applies_tag_inproject_and_lat_filters(tmp_path) -> None:
    """SearchEngine.search should honor tag, inProject and LAT filters."""
    db_path = tmp_path / "search_filters.db"
    engine = SearchEngine(str(db_path))
    manager = engine.db_manager

    now = datetime.now()

    # Model 1: recent + vehicle tag, old last_viewed, linked to a project
    model1_id = manager.add_model(
        filename="recent_vehicle.stl",
        model_format="stl",
        file_path="recent_vehicle.stl",
        file_size=123,
    )
    manager.add_model_metadata(
        model1_id,
        title="Recent Vehicle",
        description="A recent vehicle model",
        keywords="recent, vehicle",
        rating=4,
    )
    old_date = (now - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    manager.update_model_metadata(model1_id, last_viewed=old_date)
    project_id = manager.create_project("Project A")
    manager.link_model_to_project(project_id, model1_id)

    # Model 2: archive tag, very old last_viewed, not linked to any project
    model2_id = manager.add_model(
        filename="archive_part.stl",
        model_format="stl",
        file_path="archive_part.stl",
        file_size=456,
    )
    manager.add_model_metadata(
        model2_id,
        title="Archive Part",
        description="Old archive",
        keywords="archive",
        rating=3,
    )
    old_date2 = (now - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    manager.update_model_metadata(model2_id, last_viewed=old_date2)

    # Model 3: recent tag, very fresh last_viewed, not linked to any project
    model3_id = manager.add_model(
        filename="fresh_recent.stl",
        model_format="stl",
        file_path="fresh_recent.stl",
        file_size=789,
    )
    manager.add_model_metadata(
        model3_id,
        title="Fresh recent",
        description="Fresh but recent tag",
        keywords="recent",
        rating=5,
    )
    fresh_date = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    manager.update_model_metadata(model3_id, last_viewed=fresh_date)

    # Tag include: tag=recent should match models 1 and 3
    res = engine.search("", {"tags_include": ["recent"]})
    ids = {row["id"] for row in res["results"]}
    assert model1_id in ids
    assert model3_id in ids
    assert model2_id not in ids

    # Tag exclude: tag!=vehicle should exclude model 1
    res = engine.search("", {"tags_exclude": ["vehicle"]})
    ids = {row["id"] for row in res["results"]}
    assert model1_id not in ids
    assert model2_id in ids
    assert model3_id in ids

    # inProject: only models linked to at least one project
    res = engine.search("", {"in_project": True})
    ids = {row["id"] for row in res["results"]}
    assert ids == {model1_id}

    # !inProject: models not linked to any project
    res = engine.search("", {"in_project": False})
    ids = {row["id"] for row in res["results"]}
    assert model1_id not in ids
    assert model2_id in ids
    assert model3_id in ids

    # LAT>=30: models last viewed at least 30 days ago (or never) are included
    res = engine.search("", {"lat_days": 30})
    ids = {row["id"] for row in res["results"]}
    assert model1_id in ids  # 60 days old
    assert model2_id in ids  # 90 days old
    assert model3_id not in ids  # 1 day old
