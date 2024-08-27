from pathlib import Path
from .fixtures import soxcue_sheets

def test_output_paths(soxcue_sheets):
    assert soxcue_sheets[0].tracks[0].dst_path.parents[0].stem == (
        "Awesome Artist - 1969 - Awesome Album (or maybe not) [800 030-2]"
    )
    assert soxcue_sheets[0].tracks[0].dst_path.parents[1].stem == "tracks"
    assert soxcue_sheets[0].tracks[3].dst_path.name == (
        "04 - Awesome Artist - Moonchild (Including The Dream And The Illusion).flac"
    )

def test_track_properties(soxcue_sheets):
    assert soxcue_sheets[0].tracks[1].songwriter == "the best of the best"
    assert soxcue_sheets[0].tracks[2].songwriter is None
    assert soxcue_sheets[0].tracks[2].title == (
        'Epitaph (Including "March For No Reason" And "Tomorrow And Tomorrow")'
    )

def test_track_timing(soxcue_sheets):
    assert soxcue_sheets[0].tracks[2].start == 807.32
    assert soxcue_sheets[0].tracks[2].end == 1336.123
    assert soxcue_sheets[0].tracks[3].start == 1336.123
    assert soxcue_sheets[0].tracks[4].end == 0
    assert soxcue_sheets[0].tracks[2].start == 807.32


def test_track_sox_cmd(soxcue_sheets):
    path_prefix = (
        Path().cwd().joinpath("tests/data/Awesome Artist - 2024 - Awesome Album/")
    )
    assert soxcue_sheets[0].tracks[1].sox_cmd == (
        f'sox -V1 "{path_prefix}/Awesome Artist - Awesome Album.flac" '
        f'--comment="" "{path_prefix}/tracks/'
        "Awesome Artist - 1969 - Awesome Album (or maybe not) [800 030-2]/"
        '02 - Awesome Artist - I Talk To The Wind.flac" trim 443.547t =807.32t'
    )
