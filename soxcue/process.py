"""
soxcue process
"""

import os
import re
from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed as cf_as_completed,
)
import time
from datetime import timedelta
from subprocess import run, STDOUT
from mutagen import File
from mediafile import MediaFile, Image, ImageType
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.live import Live
from soxcue.sox_jobs import CueSheet, JobSpec
from soxcue.parser import TrackProperties


class SoxExecutionError(Exception):
    """SoX process execution error"""


class SoxCueProcess:
    """
    Main process and UI
    """

    def __init__(self, cue_sheets: list[CueSheet], job_spec: JobSpec, console: Console):
        """
        For each CUE sheet in the list:
        Prepare album level tags
        Start the process
        """

        self.job_spec = job_spec
        for cue_sheet in cue_sheets:

            self.tagging = {}

            if cue_sheet.cover_path:
                with open(cue_sheet.cover_path, "rb") as fh:
                    self.tagging["cover"] = Image(
                        data=fh.read(),
                        desc="album cover",
                        type=ImageType.front,
                    )
            else:
                self.tagging["cover"] = None

            if "CD" in (cd_title := cue_sheet.metadata.title.upper()):
                if disc := re.search(r"CD(?=[0-9])\d+", cd_title):
                    self.tagging["disc"] = int(disc.group(0).replace("CD", ""))
                else:
                    self.tagging["disc"] = None
            else:
                self.tagging["disc"] = None

            self.tagging["tracktotal"] = f"{len(cue_sheet.tracks):02d}"

            self.tracks_status = {
                track.index: {
                    "filename": track.dst_path.name,
                    "duration": self.get_duration(
                        (
                            track.end
                            if track.end != 0
                            else File(track.src_path).info.length
                        )
                        - track.start
                    ),
                    "status": "waiting",
                }
                for track in cue_sheet.tracks
            }
            self.process_sheet(cue_sheet, console)

    def process_sheet(self, cue_sheet: CueSheet, console: Console) -> None:
        """
        Run splitting jobs
        Update UI status
        """

        # set up a new panel for the CUE sheet
        panel_title = f"{cue_sheet.metadata.performer} - {cue_sheet.metadata.title}"
        with Live(console=console, auto_refresh=False) as live:
            text = self.get_general_info(cue_sheet, self.job_spec)

            # update UI counter
            if self.job_spec.config.time_wait > 0:
                time_text = text.copy()
                for x in range(self.job_spec.config.time_wait):
                    time_text.append(
                        f"Starting in: {self.job_spec.config.time_wait - x}\n"
                    )
                    live.update(
                        self.refresh_panel(time_text, panel_title),
                        refresh=True,
                    )
                    time.sleep(1)
                    time_text = text.copy()

            live.update(self.refresh_panel(text, panel_title), refresh=True)

            # run the jobs
            cue_sheet.tracks[0].dst_path.parent.mkdir(parents=True, exist_ok=True)

            with ProcessPoolExecutor(os.cpu_count()) as ex:
                futures = {
                    ex.submit(self.sox_process, track.sox_cmd): track.index
                    for track in cue_sheet.tracks
                }

                for future in futures:
                    self.tracks_status[futures[future]]["status"] = "sox"
                live.update(self.refresh_panel(text, panel_title), refresh=True)

                for future in cf_as_completed(futures):
                    if future.exception():
                        for future in futures:
                            future.cancel()
                        raise future.exception()

                    self.tracks_status[futures[future]]["status"] = "tagging"
                    live.update(self.refresh_panel(text, panel_title), refresh=True)

                    self.tag_file(
                        track=[
                            track
                            for track in cue_sheet.tracks
                            if track.index == futures[future]
                        ][0],
                        cue_meta=cue_sheet.metadata.__dict__,
                    )
                    self.tracks_status[futures[future]]["status"] = "done"
                    live.update(
                        self.refresh_panel(text, panel_title),
                        refresh=True,
                    )

    def refresh_panel(self, text: Text, title: str) -> Panel:
        """
        Create/update status panel
        """
        table = Table("Index", "File name", "Duration", "Status")
        for track_idx, status in self.tracks_status.items():
            table.add_row(
                track_idx,
                status["filename"],
                status["duration"],
                status["status"],
            )

        return Panel.fit(
            Columns(
                [text, table], expand=True, equal=True, column_first=True, align="left"
            ),
            title=title,
            border_style="green",
            title_align="left",
            padding=(1, 1),
        )

    def tag_file(self, cue_meta: dict, track: TrackProperties) -> None:
        """
        Tag output file
        """
        self.tagging["cue_meta"] = dict(cue_meta)
        tags = MediaFile(track.dst_path)
        tags.album = re.split(r"\s\(.+\)$", self.tagging["cue_meta"].pop("title"))[0]
        tags.artist = (
            track.performer
            if track.performer != "Unknown Artist"
            else self.tagging["cue_meta"]["performer"]
        )
        tags.albumartist = self.tagging["cue_meta"].pop("performer")
        tags.year = self.tagging["cue_meta"].pop("date")
        tags.genre = self.tagging["cue_meta"].pop("genre")
        tags.title = track.title
        tags.track = track.index
        tags.isrc = track.isrc
        tags.composer = track.songwriter
        tags.tracktotal = self.tagging["tracktotal"]
        tags.disc = self.tagging["disc"]
        tags.images = [self.tagging["cover"]] if self.tagging["cover"] else []
        tags.comments = " ".join(
            f"{k.upper()}: {v}"
            for k, v in {
                **self.tagging["cue_meta"],
                **self.job_spec.get_comments_dict(),
            }.items()
        )
        tags.save()

    @staticmethod
    def get_general_info(cue_sheet: CueSheet, job_spec: JobSpec) -> Text:
        """
        General info rich text
        """

        output_dir = (
            job_spec.config.dst_dir.joinpath(cue_sheet.tracks[0].dst_path.parent)
            if job_spec.config.dst_dir
            else cue_sheet.tracks[0].dst_path.parent
        )

        text = Text()
        text.append(f"Output Directory: {output_dir}\n")
        text.append(
            "Cover: "
            f"{cue_sheet.cover_path if cue_sheet.cover_path else 'not found'}\n\n"
        )
        text.append(f"Input file format: {cue_sheet.tracks[0].src_path.suffix}\n")
        text.append(f"Output file format: {cue_sheet.tracks[0].dst_path.suffix}\n")
        return text

    @staticmethod
    def get_duration(seconds: float) -> str:
        """
        Convert seconds count into timestamp
        """

        return str(timedelta(seconds=int(seconds)))

    @staticmethod
    def sox_process(sox_cmd: str) -> None:
        """
        Execute SoX process
        """
        run(sox_cmd, shell=True, check=True, stderr=STDOUT)
