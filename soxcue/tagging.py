"""
soxcue Tagging
"""

import re
from pathlib import Path
from mediafile import MediaFile, Image, ImageType
from soxcue.config import Config
from soxcue.sheets import SoxcueSheet
from soxcue.parser import TrackProperties


class SoxcueTaggingError(Exception):
    """soxcue tagging error"""


class Tags:
    """
    Tagging
    """

    def __init__(
        self,
        cue_sheet: SoxcueSheet,
        config: Config,
    ):
        """
        Prepare album level tags
        """

        cue_meta = dict(cue_sheet.metadata.__dict__)
        album_title = cue_meta.pop("title")
        catid = {}

        # attempt to identify cat id in the album title
        catid_re = re.compile(r"\s[\(\[].*?[0-9]{2}.*?[\)\]]$")
        if re.search(catid_re, album_title):
            catid = {"CATID": re.findall(catid_re, album_title)[0].strip("()[] ")}
            album_title = re.split(catid_re, album_title)[0]

        self.sheet_tags = {"album_title": album_title}
        self.sheet_tags["albumartist"] = cue_meta.pop("performer")
        self.sheet_tags["year"] = cue_meta.pop("date")
        self.sheet_tags["genre"] = cue_meta.pop("genre")
        self.sheet_tags["comments"] = " ".join(
            f"{k.upper()}: {v}"
            for k, v in {
                **cue_meta,
                **catid,
                **config.output_.get_comments_dict(),
            }.items()
        )

        if cue_sheet.cover_path:
            with open(cue_sheet.cover_path, "rb") as fh:
                self.sheet_tags["cover"] = Image(
                    data=fh.read(),
                    desc="album cover",
                    type=ImageType.front,
                )
        else:
            self.sheet_tags["cover"] = None

        if "CD" in (cd_title := cue_sheet.metadata.title.upper()):
            if disc := re.search(r"CD(?=[0-9])\d+", cd_title):
                self.sheet_tags["disc"] = int(disc.group(0).replace("CD", ""))
            else:
                self.sheet_tags["disc"] = None
        else:
            self.sheet_tags["disc"] = None

        self.sheet_tags["tracktotal"] = f"{len(cue_sheet.tracks):02d}"

    def get_track_tags(self, track: TrackProperties) -> dict:
        """
        Prepare output file tags
        """

        tags = {"title": track.title}
        tags["track"] = track.index
        tags["isrc"] = track.isrc
        tags["composer"] = track.songwriter
        tags["artist"] = (
            track.performer
            if track.performer != "Unknown Artist"
            else self.sheet_tags["albumartist"]
        )

        tags["album"] = self.sheet_tags["album_title"]
        tags["albumartist"] = self.sheet_tags["albumartist"]
        tags["year"] = self.sheet_tags["year"]
        tags["genre"] = self.sheet_tags["genre"]
        tags["tracktotal"] = self.sheet_tags["tracktotal"]
        tags["disc"] = self.sheet_tags["disc"]
        tags["images"] = [self.sheet_tags["cover"]] if self.sheet_tags["cover"] else []
        tags["comments"] = self.sheet_tags["comments"]

        return {"tags": tags, "path": track.dst_path}

    @staticmethod
    def write_tags(tags: dict[str, dict | Path]) -> None:
        """
        Write file tags
        """
        file_tags = MediaFile(tags["path"])
        for k, v in tags["tags"].items():
            setattr(file_tags, k, v)
        file_tags.save()
