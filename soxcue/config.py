"""
soxcue config

"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import CalledProcessError, run


class SoxcueConfigError(Exception):
    """soxcue configuration error"""


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
            raise SoxcueConfigError(f"{self.exe_name} is not installed") from exc


@dataclass
class ConfigInput:
    """
    Input config
    """

    src_path: Path


@dataclass
class ConfigOutput:
    """
    Output config
    """

    dst_dir: Path | None
    cmd_comment: str | None
    enc_format: str

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


@dataclass
class ConfigRuntime:
    """
    Runtime config
    """

    cue_encoding: str | None
    time_wait: int
    naming_spec: str
    sox: SoxProperties


@dataclass
class Config:
    """
    Config
    """

    input_: ConfigInput
    output_: ConfigOutput
    runtime_: ConfigRuntime
