from pathlib import Path
from soxcue.sox_jobs import SoxJobs
from .fixtures import metadata_tracks, get_test_cue_sheet_path


class SoxProperties:
    exe_name: str = "sox"
    comp_level: None = None
    supported_formats: list[str] = ["wav", "flac"]


class Config:
    src_path: Path = Path(get_test_cue_sheet_path())
    dst_dir: None = None
    cue_encoding: None = None
    cmd_comment: None = None
    time_wait: int = 5
    enc_format: str = "flac"
    naming_spec: str = "#c - #d - #a/#n - #p - #t"


def test_sox_jobs():
    sox_props = SoxProperties()
    config = Config()
    path_prefix = (
        Path().cwd().joinpath("tests/data/Awesome Artist - 2024 - Awesome Album/")
    )
    cue_sheets = SoxJobs(sox_props=sox_props, config=config).get_cue_sheet_jobs()

    assert cue_sheets[0].tracks[0].dst_path.parents[0].stem == (
        "Awesome Artist - 1969 - Awesome Album " "(or maybe not) [800 030-2]"
    )
    assert cue_sheets[0].tracks[0].dst_path.parents[1].stem == "tracks"
    assert cue_sheets[0].tracks[1].songwriter == "the best of the best"
    assert cue_sheets[0].tracks[2].songwriter is None
    assert cue_sheets[0].tracks[2].title == (
        'Epitaph (Including "March For No Reason" And "Tomorrow And Tomorrow")'
    )
    assert cue_sheets[0].tracks[3].dst_path.name == (
        "04 - Awesome Artist - Moonchild (Including The Dream And The Illusion).flac"
    )
    assert cue_sheets[0].tracks[2].start == 807.32
    assert cue_sheets[0].tracks[2].end == 1336.123
    assert cue_sheets[0].tracks[3].start == 1336.123
    assert cue_sheets[0].tracks[4].end == 0
    assert cue_sheets[0].tracks[2].start == 807.32
    assert cue_sheets[0].tracks[1].sox_cmd == (
        f'sox -V1 "{path_prefix}/Awesome Artist - Awesome Album.flac" '
        f'--comment="" "{path_prefix}/tracks/'
        "Awesome Artist - 1969 - Awesome Album (or maybe not) [800 030-2]/"
        '02 - Awesome Artist - I Talk To The Wind.flac" trim 443.547t =807.32t'
    )
