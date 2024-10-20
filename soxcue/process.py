"""
soxcue process
"""

import os
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)
from datetime import timedelta
from subprocess import run, STDOUT
from mutagen import File
from soxcue.sheets import SoxcueSheet
from soxcue.config import Config
from soxcue.tagging import Tags
from soxcue.status import SoxcueStatus


class SoxcueProcessError(Exception):
    """SoxcueProcess error"""


class SoxcueProcess:  # pylint: disable=too-few-public-methods
    """
    Main process and status update UI
    """

    def __init__(
        self,
        cue_sheet: SoxcueSheet,
        config: Config,
    ):
        self.tracks_status = {
            track.index: {
                "filename": track.dst_path.name,
                "duration": self._get_duration(
                    (track.end if track.end != 0 else File(track.src_path).info.length)
                    - track.start
                ),
                "status": "waiting",
            }
            for track in cue_sheet.tracks
        }
        self.tagger = Tags(cue_sheet=cue_sheet, config=config)

        executor = ThreadPoolExecutor()
        status = SoxcueStatus(
            cue_sheet=cue_sheet,
            config=config,
            tracks_status=self.tracks_status,
        )
        executor.submit(status.handler.update)
        self.process_sheet(cue_sheet=cue_sheet)
        executor.shutdown()

    def process_sheet(self, cue_sheet: SoxcueSheet) -> None:
        """
        Run splitting jobs
        """

        cue_sheet.tracks[0].dst_path.parent.mkdir(parents=True, exist_ok=True)
        with ProcessPoolExecutor(os.cpu_count() - 1) as ex:
            futures = {
                ex.submit(self._sox_process, track.sox_cmd): track.index
                for track in cue_sheet.tracks
            }

            for future in futures:
                self.tracks_status[futures[future]]["status"] = "sox"

            for future in as_completed(futures):
                if future.exception():
                    for future in futures:
                        future.cancel()
                    raise future.exception()

                self.tracks_status[futures[future]]["status"] = "tagging"

                self.tagger.write_tags(
                    self.tagger.get_track_tags(
                        track=[
                            track
                            for track in cue_sheet.tracks
                            if track.index == futures[future]
                        ][0],
                    )
                )
                self.tracks_status[futures[future]]["status"] = "done"

    @staticmethod
    def _get_duration(seconds: float) -> str:
        """
        Convert seconds count into timestamp
        """

        return str(timedelta(seconds=int(seconds)))

    @staticmethod
    def _sox_process(sox_cmd: str) -> None:
        """
        Execute SoX process
        """
        run(sox_cmd, shell=True, check=True, stderr=STDOUT)
