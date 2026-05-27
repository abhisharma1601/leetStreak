import pytest
from app.services.level_service import level_for_points, LEVELS


def test_zero_points_is_first_level():
    name, next_thresh, next_name = level_for_points(0)
    assert name == "Script Kiddie 🐣"
    assert next_thresh == 50
    assert next_name == "Code Monkey 🐒"


def test_just_below_second_level():
    name, next_thresh, _ = level_for_points(49)
    assert name == "Script Kiddie 🐣"
    assert next_thresh == 50


def test_exactly_second_level():
    name, next_thresh, next_name = level_for_points(50)
    assert name == "Code Monkey 🐒"
    assert next_thresh == 150
    assert next_name == "Algorithm Apprentice 📚"


def test_just_below_third_level():
    name, _, _ = level_for_points(149)
    assert name == "Code Monkey 🐒"


def test_exactly_third_level():
    name, next_thresh, next_name = level_for_points(150)
    assert name == "Algorithm Apprentice 📚"
    assert next_thresh == 400
    assert next_name == "DP Disciple 🧠"


def test_exactly_fourth_level():
    name, next_thresh, next_name = level_for_points(400)
    assert name == "DP Disciple 🧠"
    assert next_thresh == 800
    assert next_name == "Graph Wizard 🧙"


def test_exactly_fifth_level():
    name, next_thresh, next_name = level_for_points(800)
    assert name == "Graph Wizard 🧙"
    assert next_thresh == 1500
    assert next_name == "Big-O Sensei 🥋"


def test_just_below_max_level():
    name, next_thresh, _ = level_for_points(1499)
    assert name == "Graph Wizard 🧙"
    assert next_thresh == 1500


def test_exactly_max_level():
    name, next_thresh, next_name = level_for_points(1500)
    assert name == "Big-O Sensei 🥋"
    assert next_thresh is None
    assert next_name is None


def test_well_above_max_level():
    name, next_thresh, next_name = level_for_points(99999)
    assert name == "Big-O Sensei 🥋"
    assert next_thresh is None
    assert next_name is None


@pytest.mark.parametrize("points,expected_name", [
    (0,    "Script Kiddie 🐣"),
    (50,   "Code Monkey 🐒"),
    (150,  "Algorithm Apprentice 📚"),
    (400,  "DP Disciple 🧠"),
    (800,  "Graph Wizard 🧙"),
    (1500, "Big-O Sensei 🥋"),
])
def test_all_level_thresholds(points, expected_name):
    name, _, _ = level_for_points(points)
    assert name == expected_name
