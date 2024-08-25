"""
Generate SoX jobs

"""

import re
import os
from dataclasses import dataclass, field
from typing import Iterator
from pathlib import Path
from subprocess import CalledProcessError, run
from soxcue.parser import CueParser, CueMetaData, TrackProperties


class SoxJobsError(Exception):
    """SoxJobs error"""


@dataclass
class SoxProperties:
    """
    SoX properties
    """

    exe_name: str
    comp_level: float | None
    supported_formats: list = field(init=False)

    def __post_init__(self) -> list:
        """
        Collect audio file formats supported by SoX
        """
        formats_str = "AUDIO FILE FORMATS: "
        try:
            self.supported_formats = (
                [
                    x
                    for x in run(
                        f"{self.exe_name} -h",
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True,
                    ).stdout.split("\n")
                    if x.startswith(formats_str)
                ][0]
                .split(formats_str)[1]
                .split(" ")
            )
        except CalledProcessError as exc:
            raise SoxJobsError(f"{self.exe_name} is not installed") from exc


@dataclass
class CueSheet:
    """
    CueMetaData and TrackProperties as returned by CueParser
    with filesystem path to cue file and a cover image if found
    """

    metadata: CueMetaData
    tracks: list[TrackProperties]
    cue_path: Path
    cover_path: Path | None


@dataclass
class Config:
    """
    Job config from cmdline/defaults
    """

    src_path: Path
    dst_dir: Path | None
    cue_encoding: str | None
    cmd_comment: str | None
    time_wait: int
    enc_format: str
    naming_spec: str

    def get_comments_dict(self) -> dict:
        """
        Comments from cmdline args
        """
        if self.cmd_comment:
            comments = re.split(r"([A-Z]*:\s)", self.cmd_comment)[1:]
            return {
                k.strip(" :"): v.strip() for k, v in zip(comments[::2], comments[1::2])
            }
        return {}


class SoxJobs:
    """
    Generate SoX cmd args
    """

    def __init__(
        self,
        config: Config,
        sox_props: SoxProperties,
    ):
        """
        Verify requested destination format is supported
        Verify input path exists
        Generate CueSheet objects
        """

        if config.enc_format not in sox_props.supported_formats:
            raise SoxJobsError(
                f"Destination format '{config.enc_format}' "
                f"is not supported by {sox_props.exe_name}"
            )

        if not config.src_path.exists():
            raise SoxJobsError(f"Source path '{config.src_path}' not found")

        self.sox_props = sox_props
        self.config = config
        self.cue_sheets = [
            CueSheet(
                metadata=cue_tracks[0],
                tracks=cue_tracks[1],
                cue_path=(
                    cue_cover["cue"] if config.src_path.is_dir() else config.src_path
                ),
                cover_path=cue_cover["cover"],
            )
            for cue_cover in self.find_cue_cover(
                config.src_path if config.src_path.is_dir() else config.src_path.parent
            )
            if (
                cue_tracks := CueParser.from_file(
                    file_path=(
                        cue_cover["cue"]
                        if config.src_path.is_dir()
                        else config.src_path
                    ),
                    cue_encoding=config.cue_encoding,
                )
            )[1]
        ]

    def get_cue_sheet_jobs(self):
        """
        Generate output directories/filenames according to naming_spec
        Verify cuesheet referenced files exist and are supported by SoX
        Convert timestamps
        Assign SoX cmdlines to tracks
        """
        for cue_sheet in self.cue_sheets:
            tracks = cue_sheet.tracks
            output_filenames = [
                self.convert_spec(
                    track=track,
                    cue_sheet=cue_sheet,
                )
                for track in tracks
            ]

            # support 1 directory level in naming_spec
            if len(output_filenames[0].split("/")) == 2:
                directory_name = output_filenames[0].split("/")[0]
                output_filenames = [x.split("/")[1] for x in output_filenames]
            else:
                directory_name = ""

            tracks_count = len(tracks)
            for idx, track in enumerate(tracks):
                src_file = cue_sheet.cue_path.parent.joinpath(track.file).absolute()

                if not src_file.is_file():
                    # CUE sheet referenced file not found
                    # try other SoX supported file formats
                    for aformat in self.sox_props.supported_formats:
                        if (
                            src_file := cue_sheet.cue_path.parent.joinpath(
                                Path(f"{src_file.stem}.{aformat}")
                            ).absolute()
                        ).exists():
                            break

                # nothing we can do
                if not src_file.is_file():
                    raise SoxJobsError(
                        "Source file "
                        f"'{cue_sheet.cue_path.parent.joinpath(track.file)}' "
                        "not found or not supported by SoX"
                    )

                track.src_path = src_file
                track.start = self.stamp_to_sec(track.timestamp)

                if idx + 1 != tracks_count:
                    if tracks[idx + 1].file == track.file:
                        track.end = self.stamp_to_sec(tracks[idx + 1].timestamp)
                    else:
                        track.end = 0
                else:
                    track.end = 0

                track.dst_path = (
                    (
                        self.config.dst_dir
                        if self.config.dst_dir
                        else cue_sheet.cue_path.parent.joinpath("tracks")
                    )
                    .joinpath(
                        directory_name,
                        f"{output_filenames[idx]}.{self.config.enc_format}",
                    )
                    .absolute()
                )

                self.set_sox_cmd(track=track)

        return self.cue_sheets

    def set_sox_cmd(
        self,
        track: TrackProperties,
    ) -> None:
        """
        Form SoX cmdline
        """
        sox_cmd = [f"{self.sox_props.exe_name} -V1"]

        sox_cmd.append(f'"{track.src_path}"')

        if self.sox_props.comp_level:
            sox_cmd.append(f"-C {self.sox_props.comp_level}")

        sox_cmd.append('--comment=""')

        track_end = f" ={track.end}t" if track.end != 0 else ""
        sox_cmd.append(f'"{track.dst_path}" trim {track.start}t{track_end}')

        track.sox_cmd = " ".join(x for x in sox_cmd)

    @staticmethod
    def stamp_to_sec(timestamp: str) -> float:
        """
        Convert cue INDEX timestamp to seconds.milliseconds
        """
        minutes, seconds, frames = timestamp.split(":")
        seconds = (int(minutes) * 60) + int(seconds)

        if len(frames) == 3:
            # support non-compliant cue sheets
            # 3 digits 'frames' signify milliseconds
            return float(f"{seconds}.{frames}")

        return float(f"{seconds + (int(frames) * (1 / 75)):.3f}")

    def convert_spec(self, track: TrackProperties, cue_sheet: CueSheet) -> str:
        """
        Replace naming_spec with the appropriate CueMetaData and TrackProperties values
        Replace unsafe characters with --
        """

        def chars_re(string: str) -> str:
            return re.sub(r"[/\\?%*:|<>\x7F\x00-\x1F]", "--", string.replace('"', ""))

        naming_spec = self.config.naming_spec

        return [
            naming_spec := naming_spec.replace(a, b)
            for a, b in [
                ("#a", chars_re(cue_sheet.metadata.title)),
                ("#c", chars_re(cue_sheet.metadata.performer)),
                ("#d", chars_re(cue_sheet.metadata.date)),
                ("#n", chars_re(track.index)),
                ("#p", chars_re(track.performer)),
                ("#t", chars_re(track.title)),
            ]
        ][-1]

    @staticmethod
    def find_cue_cover(src_dir: Path) -> Iterator[dict[str, Path | None]]:
        """
        Search for .cue and covers in src_path
        """
        for root, _, files in os.walk(src_dir):
            if any(Path(file).suffix.lower() == ".cue" for file in files):
                yield {
                    "cue": Path(root).joinpath(
                        [x for x in files if Path(x).suffix.lower() == ".cue"][0]
                    ),
                    "cover": (
                        Path(root).joinpath(cover[0])
                        if (
                            cover := [
                                x
                                for x in files
                                if Path(x).suffix.lower()
                                in [
                                    ".png",
                                    ".jpg",
                                    ".jpeg",
                                ]
                                and Path(x).stem.lower()
                                in [
                                    "cover",
                                    "folder",
                                    "front",
                                ]
                            ]
                        )
                        else None
                    ),
                }
