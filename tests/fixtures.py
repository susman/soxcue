import json
import pytest
from soxcue.parser import CueMetaData, TrackProperties, CueParser


def get_test_cue_sheet_path() -> str:
    return (
        "./tests/data/Awesome Artist - 2024 - "
        "Awesome Album/Awesome Artist - Awesome Album.cue"
    )


def metadata_tracks() -> tuple[CueMetaData, list[TrackProperties]]:
    return CueParser.from_file(get_test_cue_sheet_path())


@pytest.fixture
def cue_sheet_data() -> dict:
    with open(
        "./tests/data/test_cue_sheet_data.json",
        encoding="ascii",
    ) as fh:
        return json.loads(fh.read())
