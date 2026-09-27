"""Render an upstream pygraphviz diagram through a Graphviz subprocess."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Protocol


class _DOTSource(Protocol):
    """The read-only AGraph operation required by the renderer."""

    def string(self) -> str: ...


def render_diagram(
    agraph: _DOTSource,
    filename: str | Path,
    prog: str = "dot",
    fmt: str | None = None,
) -> Path:
    """Render an AGraph as a file using an external Graphviz executable.

    The AGraph is serialized as DOT text. Its C binding is not used to draw
    the image. The executable beside the running Python environment takes
    priority; the system PATH is used when that executable is absent.
    Omitting fmt selects the filename extension, or PNG for no extension.
    The input graph is unchanged.

    Parameters
    ----------
    agraph : _DOTSource
        A pygraphviz AGraph or object exposing string() -> str.
    filename : str | Path
        Destination filename, returned as a Path.
    prog : str, default: "dot"
        Graphviz layout executable name, such as dot or neato.
    fmt : str | None, default: None
        Explicit Graphviz output format. Otherwise use the extension.

    Returns
    -------
    Path
        The requested output path after Graphviz succeeds.

    Raises
    ------
    FileNotFoundError
        If the executable is absent beside Python and from PATH.
    RuntimeError
        If Graphviz reports a nonzero exit status.

    Complexity
    ----------
    Finding a binary is O(P) for P PATH entries. Serializing and passing
    DOT costs O(D) time and memory for D characters. Graphviz layout and
    output cost depend on the selected program, graph and output format;
    this wrapper makes no tighter bound on that external process.

    References
    ----------
    Mature documentation's render_diagram helper beside show_diagram;
    ADR-0026.
    """
    output = Path(filename)
    output_format = fmt or output.suffix.lstrip(".") or "png"
    environment = Path(sys.executable).parent
    binary_name = f"{prog}.exe" if sys.platform.startswith("win") else prog
    local = environment / (
        "Library/bin" if sys.platform.startswith("win") else "bin"
    ) / binary_name
    executable = str(local) if local.is_file() else shutil.which(prog)
    if executable is None:
        raise FileNotFoundError(f"Graphviz executable not found: {prog}")

    result = subprocess.run(
        [executable, f"-T{output_format}", "-o", str(output)],
        input=agraph.string(),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Graphviz render failed: {result.stderr}")
    return output
