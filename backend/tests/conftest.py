import pytest

@pytest.fixture
def sample_deck():
    return [
        {"suit": "H", "value": "A"},
        {"suit": "S", "value": "K"},
        {"suit": "D", "value": "5"},
        {"suit": "C", "value": "2"},
        {"suit": "H", "value": "7"},
        {"suit": "S", "value": "8"},
    ]

@pytest.fixture
def mock_hand():
    return [
        {"suit": "H", "value": "A"},
        {"suit": "D", "value": "9"},
    ]
