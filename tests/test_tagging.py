from soxcue.tagging import Tags
from .fixtures import get_soxcue_sheets, get_config

cue_sheets = get_soxcue_sheets()

tags = Tags(cue_sheet=cue_sheets[0], config=get_config())

def test_tags():
    track_tags = tags.get_track_tags(cue_sheets[0].tracks[0])
    assert track_tags["tags"]["title"] == '21st Century Schizoid Man (Including "Mirrors")'
