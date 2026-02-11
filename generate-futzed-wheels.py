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


def futzed_dist_info_wheel_tag_invalid() -> tuple[str, bytes]:
    """
    Create a wheel with a `.dist-info/WHEEL` file with an invalid tag (`Tag: py3-none-futzed` instead of `Tag: py3-none-any`).
    """

    wheel_path = _make_package("futzed_dist_info_wheel_tag_invalid")
    original_data = wheel_path.read_bytes()
    output_buffer = io.BytesIO()

    with (
        zipfile.ZipFile(io.BytesIO(original_data), "r") as original_zip,
        zipfile.ZipFile(
            output_buffer, "w", compression=zipfile.ZIP_DEFLATED
        ) as new_zip,
    ):
        for item in original_zip.infolist():
            data = original_zip.read(item.filename)

            if item.filename.endswith(".dist-info/WHEEL"):
                if b"Tag: py3-none-any" not in data:
                    raise ValueError(
                        f"Expected 'Tag: py3-none-any' in {item.filename}, but it was not found"
                    )
                # Modify the WHEEL file to have incorrect tags
                data = data.replace(b"Tag: py3-none-any", b"Tag: py3-none-futzed")

            new_zip.writestr(item.filename, data)

    return (wheel_path.name, output_buffer.getvalue())


def futzed_dist_info_wheel_tag_missing() -> tuple[str, bytes]:
    """
    Create a wheel with a `.dist-info/WHEEL` file missing the `Tag:` field.
    """

    wheel_path = _make_package("futzed_dist_info_wheel_tag_missing")
    original_data = wheel_path.read_bytes()
    output_buffer = io.BytesIO()

    with (
        zipfile.ZipFile(io.BytesIO(original_data), "r") as original_zip,
        zipfile.ZipFile(
            output_buffer, "w", compression=zipfile.ZIP_DEFLATED
        ) as new_zip,
    ):
        for item in original_zip.infolist():
            data = original_zip.read(item.filename)

            if item.filename.endswith(".dist-info/WHEEL"):
                # Modify the WHEEL file to remove the Tag field
                lines = data.splitlines()
                lines = [line for line in lines if not line.startswith(b"Tag:")]
                data = b"\n".join(lines)

            new_zip.writestr(item.filename, data)

    return (wheel_path.name, output_buffer.getvalue())


def futzed_dist_info_wheel_version_invalid() -> tuple[str, bytes]:
    """
    Create a wheel with a `.dist-info/WHEEL` file with an invalid (non-PEP 440) version in the `Wheel-Version` field.
    """

    wheel_path = _make_package("futzed_dist_info_wheel_version_invalid")
    original_data = wheel_path.read_bytes()
    output_buffer = io.BytesIO()

    with (
        zipfile.ZipFile(io.BytesIO(original_data), "r") as original_zip,
        zipfile.ZipFile(
            output_buffer, "w", compression=zipfile.ZIP_DEFLATED
        ) as new_zip,
    ):
        for item in original_zip.infolist():
            data = original_zip.read(item.filename)

            if item.filename.endswith(".dist-info/WHEEL"):
                if b"Wheel-Version: 1.0" not in data:
                    raise ValueError(
                        f"Expected 'Wheel-Version: 1.0' in {item.filename}, but it was not found"
                    )
                # Modify the WHEEL file to have an invalid version
                data = data.replace(b"Wheel-Version: 1.0", b"Wheel-Version: invalid")

            new_zip.writestr(item.filename, data)

    return (wheel_path.name, output_buffer.getvalue())


def main() -> None:
    name, wheel = futzed_bz2()
    (_OUTDIR / name).write_bytes(wheel)

    name, wheel = futzed_lzma()
    (_OUTDIR / name).write_bytes(wheel)

    name, wheel = futzed_dist_info_wheel_tag_invalid()
    (_OUTDIR / name).write_bytes(wheel)

    name, wheel = futzed_dist_info_wheel_tag_missing()
    (_OUTDIR / name).write_bytes(wheel)

    name, wheel = futzed_dist_info_wheel_version_invalid()
    (_OUTDIR / name).write_bytes(wheel)


if __name__ == "__main__":
    main()
