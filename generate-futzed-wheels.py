# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///


"""
Generates a series of futzed wheels for testing purposes.

Futzes include:

* Wheels that have unusual internal compression methods (e.g., BZIP2, LZMA)
"""

import io
import subprocess
import tempfile
import zipfile
from pathlib import Path

_HERE = Path(__file__).parent
_OUTDIR = _HERE / "dist"

_OUTDIR.mkdir(exist_ok=True)


def _make_package(name: str) -> Path:
    """
    Create a new package with `uv init` and `uv build` and return the path to the built wheel.
    """

    tempdir = Path(tempfile.mkdtemp())
    pkgdir = tempdir / name

    subprocess.run(["uv", "init", name], cwd=tempdir, check=True)
    subprocess.run(["uv", "build"], cwd=pkgdir, check=True)

    dists = list((pkgdir / "dist").glob("*.whl"))
    assert len(dists) == 1, (
        f"Expected exactly one wheel in {pkgdir / 'dist'}, but found {len(dists)}"
    )
    return dists[0]


def _recompress_wheel(wheel_path: Path, compression: int) -> tuple[str, bytes]:
    """
    Recompress all entries in a wheel with the specified compression method.

    Returns a tuple of (wheel_name, wheel_bytes).
    """

    original_data = wheel_path.read_bytes()
    output_buffer = io.BytesIO()

    with (
        zipfile.ZipFile(io.BytesIO(original_data), "r") as original_zip,
        zipfile.ZipFile(output_buffer, "w", compression=compression) as new_zip,
    ):
        # Copy all entries with the new compression method
        for item in original_zip.infolist():
            data = original_zip.read(item.filename)
            new_zip.writestr(item.filename, data, compress_type=compression)

    return (wheel_path.name, output_buffer.getvalue())


def futzed_bz2() -> tuple[str, bytes]:
    """
    Create a wheel with one or more files compressed with BZIP2.
    """

    wheel_path = _make_package("futzed_bz2")
    return _recompress_wheel(wheel_path, zipfile.ZIP_BZIP2)


def futzed_lzma() -> tuple[str, bytes]:
    """
    Create a wheel with one or more files compressed with LZMA.
    """

    wheel_path = _make_package("futzed_lzma")
    return _recompress_wheel(wheel_path, zipfile.ZIP_LZMA)


def main() -> None:
    name, wheel = futzed_bz2()
    (_OUTDIR / name).write_bytes(wheel)

    name, wheel = futzed_lzma()
    (_OUTDIR / name).write_bytes(wheel)


if __name__ == "__main__":
    main()
