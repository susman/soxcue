#!/usr/bin/env python

"""
Command line parser
"""
import argparse
import shutil
import signal
import os
import textwrap
from pathlib import Path
from rich.console import Console
from soxcue.config import (
    SoxProperties,
    ConfigInput,
    ConfigOutput,
    ConfigRuntime,
    Config,
)
from soxcue.process import SoxcueProcess
from soxcue.sheets import SoxcueSheets


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
        os._exit(0)

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

    config = Config(
        input_=ConfigInput(src_path=parsed.src_path),
        output_=ConfigOutput(
            dst_dir=parsed.output_dir,
            cmd_comment=parsed.comment,
            enc_format=parsed.format,
        ),
        runtime_=ConfigRuntime(
            cue_encoding=parsed.encoding,
            time_wait=parsed.wait,
            naming_spec=parsed.naming_spec,
            sox=SoxProperties(
                exe_name=parsed.sox_exe,
                comp_level=parsed.compression_level,
            ),
        ),
    )

    if config.input_.src_path.is_dir():
        status = console.status("Searching for cue files\n")
        status.start()
        cue_sheets = SoxcueSheets(config=config).cue_sheets
        status.stop()
    else:
        cue_sheets = SoxcueSheets(config=config).cue_sheets

    for cue_sheet in cue_sheets:
        SoxcueProcess(cue_sheet=cue_sheet, config=config)


if __name__ == "__main__":
    main()
