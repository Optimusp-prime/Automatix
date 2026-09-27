"""Runtime cache compatibility and external Graphviz rendering."""

from __future__ import annotations

import gc
import shutil
import subprocess
import sys
import weakref
from pathlib import Path
from unittest.mock import patch

import pytest
from automata.fa.dfa import DFA
from cached_method import cached_method  # type: ignore[import-untyped]

import automata_extensions
from automata_extensions.utils import render_diagram
from automata_extensions.utils.patches import patch_cached_method
from tests.fa.test_state_elimination import _mature_dfa


class _Graph:
    def string(self) -> str:
        return "digraph { a -> b }"


def test_patch_is_automatic_idempotent_and_preserves_cache() -> None:
    assert automata_extensions is not None
    d = _mature_dfa()
    assert patch_cached_method() is False
    assert isinstance(DFA.isempty, cached_method)
    bound = d.isempty
    assert bound() is False
    assert bound() is False
    assert bound.cache_info().hits >= 1
    assert d.isempty.cache_info().hits >= 1


def test_mature_chained_example_and_pure_upstream() -> None:
    d = _mature_dfa()
    already_active = not patch_cached_method()
    r = (d - d).isempty()
    assert (already_active, r) == (True, True)
    assert d.difference(d).isempty() is True
    pure = DFA(**d.input_parameters)
    assert (pure - pure).isempty() is True
    assert pure.difference(pure).isempty() is True


def test_cache_does_not_retain_automaton_permanently() -> None:
    d = _mature_dfa()
    d.isempty()
    reference = weakref.ref(d)
    del d
    gc.collect()
    assert reference() is None


def test_render_infers_format_and_passes_dot_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = tmp_path / "env"
    executable = env / ("Library/bin/dot.exe" if sys.platform == "win32" else "bin/dot")
    executable.parent.mkdir(parents=True)
    executable.touch()
    monkeypatch.setattr(sys, "executable", str(env / "python.exe"))
    output = tmp_path / "figure.svg"
    with patch(
        "automata_extensions.utils.render.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    ) as run:
        result = render_diagram(_Graph(), output)
    assert result == output
    run.assert_called_once_with(
        [str(executable), "-Tsvg", "-o", str(output)],
        input="digraph { a -> b }", text=True, capture_output=True, check=False,
    )


def test_render_explicit_format_and_missing_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
    monkeypatch.setattr(shutil, "which", lambda _: "dot-in-path")
    with patch(
        "automata_extensions.utils.render.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    ) as run:
        result = render_diagram(_Graph(), tmp_path / "figure", fmt="pdf")
    assert result == tmp_path / "figure"
    assert run.call_args.args[0][1] == "-Tpdf"
    with patch(
        "automata_extensions.utils.render.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0, "", ""),
    ) as run:
        render_diagram(_Graph(), tmp_path / "figure")
    assert run.call_args.args[0][1] == "-Tpng"


def test_render_missing_binary_and_process_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(FileNotFoundError, match="dot"):
        render_diagram(_Graph(), tmp_path / "figure.png")
    monkeypatch.setattr(shutil, "which", lambda _: "dot-in-path")
    with patch(
        "automata_extensions.utils.render.subprocess.run",
        return_value=subprocess.CompletedProcess([], 1, "", "bad graph"),
    ):
        with pytest.raises(RuntimeError, match="bad graph"):
            render_diagram(_Graph(), tmp_path / "figure.png")
