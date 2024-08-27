"""
soxcue process
"""

import time
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.live import Live
from soxcue.config import Config
from soxcue.sheets import SoxcueSheet


class SoxcueStatusError(Exception):
    """soxcue status error"""


class SoxcueRich:
    """
    Rich based status updates
    """

    def __init__(
        self,
        cue_sheet: SoxcueSheet,
        config: Config,
        tracks_status: dict,
    ):

        self.tracks_status = tracks_status
        self.text = self.get_general_info(cue_sheet, config)
        self.title = f"{cue_sheet.metadata.performer} - {cue_sheet.metadata.title}"
        self.live = Live()

    def wait(self, seconds: int) -> None:
        """
        Update UI counter
        """
        current_text = self.text.copy()
        for x in range(seconds):
            self.text.append(f"Starting in: {seconds - x}\n")
            self.live.update(
                self._refresh_panel(),
                refresh=True,
            )
            time.sleep(1)
            self.text = current_text.copy()

    def update(self) -> None:
        """
        Keep updating status panel until all jobs are done
        """
        while not all(
            self.tracks_status[k]["status"] == "done" for k in self.tracks_status.keys()
        ):
            self.live.update(self._refresh_panel(), refresh=True)
            time.sleep(0.4)

        self.live.update(self._refresh_panel(), refresh=True)
        self.live.stop()

    def _refresh_panel(self) -> Panel:
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
                [self.text, table],
                expand=True,
                equal=True,
                column_first=True,
                align="left",
            ),
            title=self.title,
            border_style="green",
            title_align="left",
            padding=(1, 1),
        )

    @staticmethod
    def get_general_info(cue_sheet: SoxcueSheet, config: Config) -> Text:
        """
        General info rich text
        """

        output_dir = (
            config.output_.dst_dir.joinpath(cue_sheet.tracks[0].dst_path.parent)
            if config.output_.dst_dir
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


class SoxcueStatus:  # pylint: disable=too-few-public-methods
    """
    SoxcueStatus
    """

    def __init__(
        self,
        cue_sheet: SoxcueSheet,
        config: Config,
        tracks_status: dict,
    ):

        self.config = config
        self.tracks_status = tracks_status
        self.cue_sheet = cue_sheet
        self.handler = self._get_rich()

    def _get_rich(self) -> SoxcueRich:
        """
        Initialize SoxcueRich
        """
        soxcue_rich = SoxcueRich(
            cue_sheet=self.cue_sheet,
            config=self.config,
            tracks_status=self.tracks_status,
        )

        soxcue_rich.live.start()

        if (time_wait := self.config.runtime_.time_wait) > 0:
            soxcue_rich.wait(time_wait)

        return soxcue_rich

    def _get_logger(self):
        """
        not implemented
        """
        return
