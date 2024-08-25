#!/usr/bin/env python

"""
Command line parser
"""
import argparse
import shutil
import signal
import sys
import textwrap
from pathlib import Path
from rich.traceback import install
from rich.console import Console
from soxcue.sox_jobs import SoxJobs, SoxProperties, Config
from soxcue.process import SoxCueProcess

install(show_locals=True)


class SoxcueError(Exception):
    """SoxcueError"""


def main() -> None:
    """
    Parse cmd args
    Prepare work env info
    Run the process
    """

    console = Console()

    # pylint: disable=unused-argument
    def signal_handler(sig, frame) -> None:
        """
        Handle ctrl+c
        """
        # take cli cursor back from rich
        console.show_cursor(show=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    argparser = argparse.ArgumentParser(
        prog="soxcue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Naming format:
                #a = Album Title (top level TITLE)
                #c = CD/Album Performer (top level PERFORMER)
                #d = Date (REM DATE)
                #n = Track Index
                #p = Track Performer
                #t = Track Title

            Default tags:
                Unknown Album/Artist/Title/Genre
                Default Year: 1900
            """
        ),
    )
    argparser.add_argument(
        "src_path",
        help="path to a CUE file or a directory",
        type=Path,
    )
    argparser.add_argument(
        "-c",
        "--comment",
        help="additional comments in the format of 'KEY: VALUE NKEY: NVALUE'",
        type=str,
        default=None,
    )
    argparser.add_argument(
        "-C",
        "--compression-level",
        help="SoX compression level. Default: SoX default",
        type=float,
        default=None,
    )
    argparser.add_argument(
        "-d",
        "--output-dir",
        help="path to an output directory. Default: <CUE sheet parent directory>/tracks",
        type=Path,
        default=None,
    )
    argparser.add_argument(
        "-e",
        "--encoding",
        help="CUE sheet file encoding. Default: detected by chardet",
        type=str,
        default=None,
    )
    argparser.add_argument(
        "-f",
        "--format",
        help="output file format (supported by SoX). Default: flac",
        type=str,
        default="flac",
    )
    argparser.add_argument(
        "-n",
        "--naming-spec",
        help=("output naming format. Default: '#c - #d - #a/#n - #p - #t'"),
        type=str,
        default="#c - #d - #a/#n - #p - #t",
    )
    argparser.add_argument(
        "-s",
        "--sox-exe",
        help="SoX command name (or full path to an executable). Default: sox",
        type=str,
        default="sox",
    )
    argparser.add_argument(
        "-w",
        "--wait",
        help="delay each CUE sheet processing by x seconds. Default: 5",
        type=int,
        default=5,
    )
    parsed = argparser.parse_args()

    if not shutil.which(parsed.sox_exe):
        raise SoxcueError(f"{parsed.sox_exe} command not found\n")

    sox_props = SoxProperties(
        exe_name=parsed.sox_exe,
        comp_level=parsed.compression_level,
    )
    config = Config(
        src_path=parsed.src_path,
        cmd_comment=parsed.comment,
        dst_dir=parsed.output_dir,
        cue_encoding=parsed.encoding,
        enc_format=parsed.format,
        naming_spec=parsed.naming_spec,
        time_wait=parsed.wait,
    )

    if config.src_path.is_dir():
        status = console.status("Searching for cue files\n")
        status.start()
        cue_sheets = SoxJobs(sox_props=sox_props, config=config).get_cue_sheet_jobs()
        status.stop()
    else:
        cue_sheets = SoxJobs(sox_props=sox_props, config=config).get_cue_sheet_jobs()

    SoxCueProcess(cue_sheets=cue_sheets, config=config, console=console)


if __name__ == "__main__":
    main()
