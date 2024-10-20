import json
import pytest
from pathlib import Path
from soxcue.parser import CueMetaData, TrackProperties, CueParser
from soxcue.sheets import SoxcueSheets

def get_test_cue_sheet_path() -> str:
    return (
        "./tests/data/Awesome Artist - 2024 - "
        "Awesome Album/Awesome Artist - Awesome Album.cue"
    )

class SoxProperties:
    exe_name: str = "sox"
    comp_level: None = None
    supported_formats: list[str] = ["wav", "flac"]

class ConfigInput:
    src_path: Path = Path(get_test_cue_sheet_path())

class ConfigOutput:
    dst_dir: None = None
    cmd_comment: None = None
    enc_format: str = "flac"

    def get_comments_dict(self):
        return {}

class ConfigRuntime:
    cue_encoding: None = None
    time_wait: int = 5
    naming_spec: str = "#c - #d - #a/#n - #p - #t"
    sox: SoxProperties = SoxProperties()

class Config:
    input_: ConfigInput = ConfigInput()
    output_: ConfigOutput = ConfigOutput()
    runtime_: ConfigRuntime = ConfigRuntime()


def get_metadata_tracks() -> tuple[CueMetaData, list[TrackProperties]]:
    return CueParser.from_file(get_test_cue_sheet_path())

def get_config() -> Config:
    return Config

def get_soxcue_sheets() -> list:
    return SoxcueSheets(config=Config).cue_sheets

@pytest.fixture
def cue_sheet_data() -> dict:
    with open(
        "./tests/data/test_cue_sheet_data.json",
        "r",
    ) as fh:
        return json.loads(fh.read())

@pytest.fixture
def soxcue_sheets() -> list:
    return SoxcueSheets(config=Config).cue_sheets
