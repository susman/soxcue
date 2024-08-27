# soxcue
Convert cue sheet + audio file(s) to tagged tracks.
Based on [SoX](https://sourceforge.net/projects/sox/), the tool reads CUE sheets and extracts individual tracks from the corresponding audio file(s).

The project started as a [deflacue](https://github.com/idlesign/deflacue) fork but quickly turned into a complete rewrite.

Features:
- Input any file format/sample rate SoX supports
- Output any formats SoX and [mediafile](https://github.com/beetbox/mediafile) support
- "cover, folder, front"."png, jpg, jpeg" file found next to CUE sheet will be used as a cover image
- [rich](https://github.com/Textualize/rich) based status UI
- [chardet](https://github.com/chardet/chardet) based CUE sheet decoding
- Multiprocessing (*CPUs - 1) for tracks extraction
- Preserves any REM (other than GENRE and DATE) commands as comments
- Output directory and filename templating
- `src_path` can be either a directory or a CUE sheet file
- Support for milliseconds (000-999) in INDEX timestamps (e.g `15:03:017`) for manually created CUE sheets

## Installation
Only Unix-like is supported. Might work on WSL.

With your favourite package manager:
1. install Python >= 3.11
2. install required Python packages: `pip`, `chardet`, `rich`, `mediafile`
3. install `git`
4. install `sox`

Debian/based example (as **root**):
```bash
apt update; apt install -y --no-install-recommends python3-pip python3-chardet python3-rich python3-mediafile git sox
```

With `pip` as **non-root** user:
1. make sure your `~/.local/bin` is in your `PATH`, then:
```bash
pip install --user --break-system-packages git+https://github.com/susman/soxcue.git
```

## Basic usage
Read the help message
```bash
soxcue --help
```
Path to a CUE sheet file or a directory is the only required argument.
If path to a CUE sheet file is specified, the tool will create `<CUE sheet parent directory>/tracks/` directory and, following the default naming template `'#c - #d - #a/#n - #p - #t'`, an additional directory named as `<CD/Album Performer> - <Date (REM DATE)> - <Album Title>` in it. This directory will contain the resulting files named as `<Track Index> - <Track Performer> - <Track Title>.flac`.
The same will happen if path to a directory is specified, only for every CUE sheet file found in the directory (recursively).

## Advanced usage
TODO

## Using CUE parser in your code
```python
from soxcue.parser import CueMetaData, TrackProperties, CueParser

metadata, tracks = CueParser.from_file("/path/to/Awesome Artist - Awesome Album.cue")
metadata: CueMetaData = metadata
tracks: list[TrackProperties] = tracks

# metadata.__dict__ for arbitrary REM commands
```
