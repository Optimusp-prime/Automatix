"""MP4 export of real DFA executions through Graphviz and optional FFmpeg."""

from __future__ import annotations

import json
import os
import math
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from automata_extensions.fa.dfa_mixins.animation import (
    AnimationMixin,
    _find_ffmpeg,
    _find_video_executable,
)
from automata_extensions.fa.dfa_mixins import animation_video
from tests.fa.test_state_elimination import _mature_dfa


def _partial_dfa() -> ExtendedDFA:
    return ExtendedDFA(
        states={"start", "end"}, input_symbols={"a"},
        transitions={"start": {"a": "end"}, "end": {}},
        initial_state="start", final_states={"end"}, allow_partial=True,
    )


def test_api_scope_and_html_contract() -> None:
    assert ExtendedDFA.export_animation_video is AnimationMixin.export_animation_video
    assert ExtendedDFA.__mro__.count(AnimationMixin) == 1
    assert not hasattr(ExtendedNFA, "export_animation_video")
    assert not hasattr(ExtendedGNFA, "export_animation_video")
    assert "data-frames" in _mature_dfa().animate("aab")


@pytest.mark.parametrize("fps", [0.0, -1.0, math.nan, math.inf, -math.inf])
def test_invalid_frame_rate_is_rejected_before_render(
    tmp_path: Path, fps: float,
) -> None:
    with patch(
        "automata_extensions.fa.dfa_mixins.animation._find_ffmpeg",
        side_effect=AssertionError("FFmpeg lookup must not run"),
    ):
        with pytest.raises(ValueError, match="fps"):
            _mature_dfa().export_animation_video("a", tmp_path / "x.mp4", fps=fps)


def test_suffix_and_parent_validation(tmp_path: Path) -> None:
    d = _mature_dfa()
    with pytest.raises(ValueError, match=".mp4"):
        d.export_animation_video("a", tmp_path / "x.txt")
    with pytest.raises(FileNotFoundError, match="destination directory"):
        d.export_animation_video("a", tmp_path / "missing" / "x.mp4")


@pytest.mark.parametrize("destination", ["default", "directory", "filename"])
def test_real_export_without_path_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str,
) -> None:
    # The notebook kernel knows its interpreter, even when its PATH was not
    # activated by Conda. Exercise both real tools, not a mocked renderer.
    environment = Path(sys.executable).parent
    binaries = environment / "Library" / "bin" if sys.platform.startswith("win") else environment
    if not all((binaries / (name + (".exe" if sys.platform.startswith("win") else ""))).is_file()
               for name in ("dot", "ffmpeg")):
        pytest.skip("Graphviz and FFmpeg must be installed in the Python environment")
    monkeypatch.setenv("PATH", "")
    monkeypatch.chdir(tmp_path)
    before = dict(os.environ)
    d = _partial_dfa()
    if destination == "default":
        output = d.export_animation_video("a", render_fps=2)
        expected = tmp_path / "animation.mp4"
    elif destination == "directory":
        folder = tmp_path / "videos with spaces"
        folder.mkdir()
        output = d.export_animation_video("a", folder, render_fps=2)
        expected = folder / "animation.mp4"
    else:
        output = d.export_animation_video("a", tmp_path / "custom.mp4", render_fps=2)
        expected = tmp_path / "custom.mp4"
    assert output.resolve() == expected
    assert expected.read_bytes()[4:8] == b"ftyp"
    assert dict(os.environ) == before
    assert not list(tmp_path.rglob(".automatix-video-*"))


def test_graphviz_missing_explains_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(sys, "executable", "/no-such-environment/python")
    with pytest.raises(RuntimeError, match="Graphviz"):
        animation_video._layout_once("digraph { a -> b }")


@pytest.mark.parametrize("name", ["dot", "ffmpeg"])
def test_explicit_environment_does_not_fall_back_to_path(tmp_path: Path, name: str) -> None:
    environment = tmp_path / "chosen env"
    binary_dir = environment / "Library" / "bin" if sys.platform.startswith("win") else environment / "bin"
    binary_dir.mkdir(parents=True)
    binary = binary_dir / (name + (".exe" if sys.platform.startswith("win") else ""))
    with patch("automata_extensions.fa.dfa_mixins.animation.shutil.which", return_value="wrong-env"):
        assert _find_video_executable(name, environment) is None
        binary.touch()
        assert _find_video_executable(name, environment) == str(binary)


def test_invalid_environment_fails_before_render(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="environment"):
        _partial_dfa().export_animation_video("a", tmp_path / "out.mp4", env_path=tmp_path / "absent")
    assert not (tmp_path / "out.mp4").exists()


def test_real_export_uses_selected_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment = Path(sys.prefix)
    binary_dir = environment / "Library" / "bin" if sys.platform.startswith("win") else environment / "bin"
    if not all((binary_dir / (name + (".exe" if sys.platform.startswith("win") else ""))).is_file()
               for name in ("dot", "ffmpeg")):
        pytest.skip("selected environment needs real Graphviz and FFmpeg")
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(sys, "executable", str(tmp_path / "other-env" / "python.exe"))
    before = dict(os.environ)
    output = _partial_dfa().export_animation_video(
        "a", tmp_path / "chosen.mp4", env_path=str(environment), render_fps=2,
    )
    assert output.read_bytes()[4:8] == b"ftyp"
    assert dict(os.environ) == before


@pytest.mark.parametrize("render_fps", [0, -1, 2.5, True])
def test_render_frame_rate_must_be_positive_integer(
    tmp_path: Path, render_fps: int,
) -> None:
    with pytest.raises(ValueError, match="render_fps"):
        _mature_dfa().export_animation_video(
            "a", tmp_path / "x.mp4", render_fps=render_fps,
        )


def test_ffmpeg_absent_is_clear_and_does_not_create_file(tmp_path: Path) -> None:
    target = tmp_path / "animation.mp4"
    with patch("automata_extensions.fa.dfa_mixins.animation._find_ffmpeg", return_value=None):
        with pytest.raises(RuntimeError, match="FFmpeg is required"):
            _mature_dfa().export_animation_video("aab", target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_ffmpeg_lookup_uses_path_then_active_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with patch("automata_extensions.fa.dfa_mixins.animation.shutil.which", return_value="on-path"):
        assert _find_ffmpeg() == "on-path"
    environment = tmp_path / "env"
    candidate = (
        environment / "Library" / "bin" / "ffmpeg.exe"
        if sys.platform.startswith("win") else environment / "ffmpeg"
    )
    candidate.parent.mkdir(parents=True)
    candidate.touch()
    monkeypatch.setattr(sys, "executable", str(environment / "python.exe"))
    with patch("automata_extensions.fa.dfa_mixins.animation.shutil.which", return_value=None):
        assert _find_ffmpeg() == str(candidate)


def test_mocked_frames_and_process_contract(tmp_path: Path) -> None:
    d = _partial_dfa()
    before = deepcopy(d.input_parameters)
    commands: list[list[str]] = []
    rendered: list[tuple[object, ...]] = []

    def fake_frames(*args: object) -> int:
        rendered.append(args)
        folder = cast(Path, args[-1])
        for index in range(12):
            (folder / f"frame_{index:06d}.png").write_bytes(b"png")
        return 12

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert "shell" not in kwargs
        assert kwargs["check"] is False
        frames = sorted(Path(command[-1]).parent.glob("frame_*.png"))
        assert len(frames) == 12
        Path(command[-1]).write_bytes(b"encoded mp4")
        return subprocess.CompletedProcess(command, 0, "", "")

    output = tmp_path / "result.mp4"
    with (
        patch("automata_extensions.fa.dfa_mixins.animation._find_ffmpeg", return_value="ffmpeg"),
        patch("automata_extensions.fa.dfa_mixins.animation_video.write_video_frames",
              side_effect=fake_frames),
        patch("automata_extensions.fa.dfa_mixins.animation.subprocess.run", side_effect=fake_run),
    ):
        assert d.export_animation_video("aa", output, fps=2.5, render_fps=30) == output

    assert output.read_bytes() == b"encoded mp4"
    assert d.input_parameters == before
    assert list(tmp_path.iterdir()) == [output]
    assert len(commands) == 1 and commands[0][0] == "ffmpeg"
    assert commands[0][commands[0].index("-framerate") + 1] == "30"
    assert len(rendered) == 1
    assert rendered[0][2] == "aa" and rendered[0][6:8] == (2.5, 30)
    assert rendered[0][1] == d.execution_trace("aa")


def test_failed_encoder_preserves_existing_file_and_cleans_frames(tmp_path: Path) -> None:
    target = tmp_path / "existing.mp4"
    target.write_bytes(b"old video")
    with (
        patch("automata_extensions.fa.dfa_mixins.animation._find_ffmpeg", return_value="ffmpeg"),
        patch("automata_extensions.fa.dfa_mixins.animation_video.write_video_frames",
              return_value=1),
        patch(
            "automata_extensions.fa.dfa_mixins.animation.subprocess.run",
            return_value=subprocess.CompletedProcess([], 1, "", "codec unavailable"),
        ) as run,
    ):
        with pytest.raises(RuntimeError, match="codec unavailable"):
            _mature_dfa().export_animation_video("", target)
    assert "shell" not in run.call_args.kwargs
    assert target.read_bytes() == b"old video"
    assert list(tmp_path.iterdir()) == [target]


def test_heterogeneous_states_without_direct_sorting(tmp_path: Path) -> None:
    d = ExtendedDFA(
        states={1, ("done",), None}, input_symbols={"a"},
        transitions={1: {"a": ("done",)}, ("done",): {"a": ("done",)}, None: {}},
        initial_state=1, final_states={("done",)}, allow_partial=True,
    )
    recorded: list[tuple[object, ...]] = []

    def fake_frames(*args: object) -> int:
        recorded.append(args)
        return 2

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        Path(command[-1]).write_bytes(b"mp4")
        return subprocess.CompletedProcess(command, 0, "", "")

    with (
        patch("automata_extensions.fa.dfa_mixins.animation._find_ffmpeg", return_value="ffmpeg"),
        patch("automata_extensions.fa.dfa_mixins.animation_video.write_video_frames",
              side_effect=fake_frames),
        patch("automata_extensions.fa.dfa_mixins.animation.subprocess.run", side_effect=fake_run),
    ):
        assert d.export_animation_video("a", tmp_path / "heterogeneous.mp4").exists()
    assert len(recorded) == 1
    assert recorded[0][1] == d.execution_trace("a")


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None
    or shutil.which("dot") is None,
    reason="real FFmpeg, ffprobe and Graphviz are required",
)
@pytest.mark.parametrize(
    ("word", "partial"),
    [("", False), ("aaa", False), ("aab", False),
     ("bbb", False), ("aa", True)],
)
def test_real_mp4_is_decodable(
    tmp_path: Path, word: str, partial: bool,
) -> None:
    d = _partial_dfa() if partial else _mature_dfa()
    before = deepcopy(d.input_parameters)
    result = d.export_animation_video(word, tmp_path / "actual.mp4", render_fps=8)
    assert result.exists() and result.stat().st_size > 0
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,nb_read_frames",
         "-of", "json", str(result)],
        capture_output=True, text=True, check=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert stream["codec_name"] == "h264"
    assert (stream["width"], stream["height"]) == (1280, 720)
    assert stream["r_frame_rate"] == "8/1"
    assert int(stream["nb_read_frames"]) > len(word) + 1
    assert d.input_parameters == before
    assert list(tmp_path.iterdir()) == [result]
