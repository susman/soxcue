#!/usr/bin/env python

import signal
import sys
import argparse
import os
import textwrap
from pathlib import Path
from rich.traceback import install
from rich.console import Console
from soxcue.sox_jobs import JobSpec, SoxJobs, SoxProperties, Config
from soxcue.process import SoxCueProcess

install(show_locals=True)


class SoxCueError(Exception):
    """SoxCueError"""


def main() -> None:

    console = Console()

    # pylint: disable=unused-argument
    def signal_handler(sig, frame) -> None:
        console.show_cursor(show=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    argparser = argparse.ArgumentParser(
        prog="soxcue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Namig format:
                #a = Album Title (top level TITLE)
                #c = Album Performer (top level PERFORMER)
                #d = Year (REM DATE)
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
        help="path to cue file or directory",
        type=Path,
    )
    argparser.add_argument(
        "-d",
        "--output-dir",
        help="path to output directory. Default: <cue sheet directory>/tracks",
        type=Path,
        default=None,
    )
    argparser.add_argument(
        "-e",
        "--encoding",
        help="cue sheet file encoding. Default: detected by chardet",
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
        "-w",
        "--wait",
        help="delay cue sheet processing by x seconds. Default: 5",
        type=int,
        default=5,
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
        "-s",
        "--sox-exe",
        help="SoX executable. Default: sox",
        type=str,
        default="sox",
    )

    parsed = argparser.parse_args()
    sox_props = SoxProperties(
        exe_name=parsed.sox_exe,
        comp_level=parsed.compression_level,
    )

    if os.system(f"command -v {sox_props.exe_name} 2>&1>/dev/null") != 0:
        raise SoxCueError(f"{sox_props.exe_name} command not found\n")

    config = Config(
        src_path=parsed.src_path,
        cmd_comment=parsed.comment,
        dst_dir=parsed.output_dir,
        cue_encoding=parsed.encoding,
        dst_aformat=parsed.format,
        format_spec=parsed.naming_spec,
        time_wait=parsed.wait,
    )

    job_spec = JobSpec(
        sox_props=sox_props,
        config=config,
    )
    if config.src_path.is_dir():
        status = console.status("Searching for cue files\n")
        status.start()
        cue_sheets = SoxJobs(job_spec=job_spec).prepare_jobs()
        status.stop()
    else:
        cue_sheets = SoxJobs(job_spec=job_spec).prepare_jobs()

    SoxCueProcess(cue_sheets=cue_sheets, job_spec=job_spec, console=console)


if __name__ == "__main__":
    main()
