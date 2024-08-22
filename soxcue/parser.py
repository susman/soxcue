"""
Cue file parser
"""

from dataclasses import dataclass
from pathlib import Path
import chardet


class ParserError(Exception):
    """Cue file parser error"""


@dataclass
class CueMetaData:
    """
    Cue sheet top level metadata:
    REM commands
    PERFORMER and TITLE commands
    """

    title: str = "Unknown Album"
    performer: str = "Unknown Artist"
    genre: str = "Unknown Genre"
    date: str = "1900"


@dataclass
class TrackProperties:
    """
    Track properties
    """

    title: str = "Unknown Title"
    performer: str = "Unknown Artist"
    file: str | None = None
    index: str | None = None
    timestamp: str | None = None
    isrc: str | None = None
    songwriter: str | None = None


class CueParser:
    """
    Cue sheet file parser
    Read lines as returned by open.readlines()
    Populate CueMetaData and TrackProperties with parsed data
    """

    def __init__(self, cue_sheet_lines: list[str]):
        self.cue_lines = [x.strip() for x in cue_sheet_lines]

    def parse_cue_sheet(self) -> tuple[CueMetaData, list[TrackProperties]]:
        """
        Parse cue sheet lines
        Return CueSheet
        """
        cue_metadata = CueMetaData()
        tracks = []

        for cue_line in self.cue_lines:
            cue_line = cue_line.strip().partition(" ")

            if not tracks:
                if cue_line[0] == "REM":
                    setattr(
                        cue_metadata,
                        cue_line[2].partition(" ")[0].strip().lower(),
                        cue_line[2].partition(" ")[2].strip().replace('"', ""),
                    )
                    continue
                if cue_line[0] == "PERFORMER":
                    cue_metadata.performer = cue_line[2].strip().replace('"', "")
                    continue
                if cue_line[0] == "TITLE":
                    cue_metadata.title = cue_line[2].strip().replace('"', "")
                    continue

            if cue_line[0] == "FILE":
                current_file = cue_line[2].split('"')[1]
            elif (
                cue_line[0] == "TRACK"
                and (index := cue_line[2].partition(" "))[2] == "AUDIO"
            ):
                track = TrackProperties()
                track.index = index[0]
                track.file = current_file
                tracks.append(track)
            elif cue_line[0] == "PERFORMER":
                tracks[-1].performer = cue_line[2].replace('"', "").strip()
            elif cue_line[0] == "TITLE":
                tracks[-1].title = cue_line[2].replace('"', "").strip()
            elif cue_line[0] == "ISRC":
                tracks[-1].isrc = cue_line[2].replace('"', "").strip()
            elif cue_line[0] == "SONGWRITER":
                tracks[-1].songwriter = cue_line[2].replace('"', "").strip()
            elif (
                cue_line[0] == "INDEX"
                and (timestamp := cue_line[2].partition(" "))[0] == "01"
            ):
                tracks[-1].timestamp = timestamp[2]

        return (cue_metadata, tracks)

    @staticmethod
    def from_file(
        file_path: str, cue_encoding: str = None
    ) -> tuple[CueMetaData, list[TrackProperties]]:
        """
        Attempt to read a cue file and parse it
        """
        cue_file = Path(file_path).absolute()

        if not cue_encoding:
            with open(cue_file, "rb") as fh:
                cue_encoding = chardet.detect(fh.read())["encoding"]

        with open(cue_file, encoding=cue_encoding) as fh:
            try:
                lines = fh.readlines()
            except UnicodeDecodeError as exc:
                raise ParserError(
                    "Couldn't decode cue sheet file, "
                    "try to specify the encoding explicitly"
                ) from exc

        return CueParser(lines).parse_cue_sheet()
