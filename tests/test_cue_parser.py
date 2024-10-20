from .fixtures import cue_sheet_data, get_metadata_tracks


metadata, tracks = get_metadata_tracks()

def test_cue_metadata(cue_sheet_data):
    for k, v in cue_sheet_data["metadata"].items():
        if value := getattr(metadata, k):
            assert value == v
        else:
            assert metadata.__dict__[k] == v

def test_track_props(cue_sheet_data):
    for idx, track in enumerate(cue_sheet_data["tracks"]):
        for k, v in track.items():
            if value := getattr(tracks[idx], k):
                assert value == v
            else:
                assert tracks[idx].__dict__[k] == v
