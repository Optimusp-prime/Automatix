"""Stable Graphviz geometry and smoothly sampled DFA video moments."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageColor

import pytest

from automata_extensions.fa.dfa_mixins.animation_video import (
    _FrameRenderer,
    _Moment,
    _centered_text,
    _layout_from_plain,
    _point_at,
    _timeline,
    write_video_frames,
)


_PLAIN = """graph 1 2 1.5
node __start__ 0.05 0.4 0.05 0.05 __start__ invis point black lightgrey
node s0 0.5 0.5 0.5 0.5 q0 solid circle black white
node s1 1.5 0.5 0.6 0.6 q1 solid doublecircle black white
edge __start__ s0 4 0.08 0.4 0.1 0.4 0.2 0.45 0.25 0.5 solid black
edge s0 s1 4 0.75 0.5 0.9 0.5 1.1 0.5 1.2 0.5 a 1.0 0.7 solid black
edge s1 s1 7 1.4 0.8 1.35 1.0 1.4 1.2 1.5 1.2 1.6 1.2 1.65 1.0 1.7 0.8 b 1.6 1.3 solid black
stop
"""


def _rgb(image: Image.Image, point: tuple[int, int]) -> tuple[int, int, int]:
    pixel = image.getpixel(point)
    assert isinstance(pixel, tuple) and len(pixel) == 3
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def test_plain_layout_keeps_nodes_edges_and_loop_geometry() -> None:
    first = _layout_from_plain(_PLAIN)
    assert first == _layout_from_plain(_PLAIN)
    assert set(first.nodes) == {"s0", "s1"}
    assert first.nodes["s1"].final
    assert first.nodes["s0"].x < first.nodes["s1"].x
    assert len(first.edges) == 3  # Initial arrow, transition, self-loop.
    transition = first.transition("s0", "s1", "a")
    loop = first.transition("s1", "s1", "b")
    assert len(transition.samples) > len(transition.points)
    assert len(loop.samples) > len(loop.points)
    early, _ = _point_at(loop.samples, 0.2)
    late, _ = _point_at(loop.samples, 0.8)
    assert early != late


def test_timeline_has_motion_arrival_pulse_and_stable_states() -> None:
    identifiers = {"q0": "s0", "q1": "s1"}
    transitions = {"q0": {"a": "q1"}, "q1": {"b": "q1"}}
    trace = ["q0", "q1", "q1"]
    moments = list(_timeline(trace, "ab", transitions, identifiers, 1.0, 10))
    assert moments == list(_timeline(trace, "ab", transitions, identifiers, 1.0, 10))
    assert len(moments) > len(trace)
    assert moments[0].step == 0 and moments[0].state_id == "s0"
    first_edge = [moment for moment in moments if moment.edge == ("s0", "s1", "a")]
    assert len(first_edge) > 1
    assert first_edge[0].progress < first_edge[-1].progress
    assert any(moment.pulse > 0 for moment in first_edge)
    assert any(moment.edge == ("s1", "s1", "b") for moment in moments)
    assert moments[-1].final and moments[-1].state_id == "s1"


def test_partial_failure_and_empty_word_keep_last_real_state() -> None:
    identifiers = {"q0": "s0", "q1": "s1"}
    transitions = {"q0": {"a": "q1"}, "q1": {}}
    blocked = list(_timeline(["q0", "q1", None], "ab",
                             transitions, identifiers, 1.0, 10))
    assert blocked[-1].final and blocked[-1].blocked_at == 1
    assert blocked[-1].state_id == "s1"
    assert any(moment.blocked_at == 1 and moment.edge is None for moment in blocked)
    empty = list(_timeline(["q0"], "", transitions, identifiers, 1.0, 10))
    assert len(empty) > 1
    assert empty[0].state_id == empty[-1].state_id == "s0"
    assert empty[-1].final


def test_frame_renders_two_outcomes_without_repositioning_graph() -> None:
    layout = _layout_from_plain(_PLAIN)
    accepted = _FrameRenderer(layout, "a", True)
    rejected = _FrameRenderer(layout, "a", False)
    initial = _Moment(0, "s0", 0, None, 0.0, 0.0, False, None)
    moving = _Moment(1, "s0", 0, ("s0", "s1", "a"), 0.5, 0.0, False, None)
    final = _Moment(1, "s1", None, None, 0.0, 0.0, True, None)
    before_nodes = dict(layout.nodes)
    image_initial = accepted.frame(initial)
    image_moving = accepted.frame(moving)
    assert image_initial.size == image_moving.size == (1280, 720)
    assert ImageChops.difference(image_initial, image_moving).getbbox() is not None
    assert dict(layout.nodes) == before_nodes
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._centered_text",
        wraps=_centered_text,
    ) as text:
        accepted.frame(final)
        rejected.frame(final)
    messages = [call.args[2] for call in text.call_args_list]
    assert "Accepté" in messages and "Refusé" in messages


def test_word_is_top_left_and_consumed_prefix_is_dimmed() -> None:
    renderer = _FrameRenderer(_layout_from_plain(_PLAIN), "abbb", False)
    final = _Moment(1, "s1", None, None, 0, 0, True, 1)
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._centered_text",
        wraps=_centered_text,
    ) as text:
        frame = renderer.frame(final)
    cells = [c for c in text.call_args_list if c.args[2] in {"a", "b"}
             and c.args[1][1] < 280]
    assert [c.args[2] for c in cells] == list("abbb")
    assert cells[0].args[1][0] < 240
    consumed = ImageColor.getrgb(cells[0].args[4])
    unread = ImageColor.getrgb(cells[1].args[4])
    assert min(consumed[:3]) > 175  # 25% text opacity on the light background.
    assert max(unread[:3]) < 100  # Full-opacity glyph, not faded with the prefix.
    for x in (142, 194, 246):
        red, green, blue = _rgb(frame, (x, 114))
        assert red > green + 40 and red > blue + 40
    red, green, _ = _rgb(frame, (90, 114))
    assert red < green  # Consumed prefix retains its teal underline.


def test_final_nonaccepting_state_marks_only_last_symbol() -> None:
    renderer = _FrameRenderer(_layout_from_plain(_PLAIN), "aba", False)
    frame = renderer.frame(_Moment(3, "s0", None, None, 0, 0, True, None))
    for x in (90, 142):
        red, green, _ = _rgb(frame, (x, 114))
        assert red < green
    red, green, blue = _rgb(frame, (194, 114))
    assert red > green + 40 and red > blue + 40


@pytest.mark.parametrize("blocked_at", [None, 0])
def test_all_rejections_use_same_minimal_verdict(blocked_at: int | None) -> None:
    renderer = _FrameRenderer(_layout_from_plain(_PLAIN), "a", False)
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._centered_text",
        wraps=_centered_text,
    ) as text:
        renderer.frame(_Moment(0 if blocked_at == 0 else 1, "s0", None,
                               None, 0, 0, True, blocked_at))
    messages = [c.args[2] for c in text.call_args_list]
    assert "Refusé" in messages
    assert not any("Bloqué" in m or "MOT" in m or "Transition" in m for m in messages)


def test_timeline_eases_travel_and_counts_only_consumed_symbols() -> None:
    moments = list(_timeline(["q0", "q1"], "a", {"q0": {"a": "q1"}},
                             {"q0": "s0", "q1": "s1"}, 1, 60))
    moving = [m for m in moments if m.edge is not None]
    assert moving[0].step == 0
    assert moving[-1].step == 1
    progress = [m.progress for m in moving]
    assert progress == sorted(progress)
    assert progress[2] - progress[1] < progress[25] - progress[24]
    assert progress[-1] == 1


@pytest.mark.parametrize("accepted", [True, False])
def test_empty_word_shows_epsilon_in_top_left_without_rejection_cell(accepted: bool) -> None:
    renderer = _FrameRenderer(_layout_from_plain(_PLAIN), "", accepted)
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._centered_text",
        wraps=_centered_text,
    ) as text:
        renderer.frame(_Moment(0, "s0", None, None, 0, 0, True, None))
    epsilon = [c for c in text.call_args_list if c.args[2] == "ε"]
    assert len(epsilon) == 1 and epsilon[0].args[1][0] < 240
    assert epsilon[0].args[1][1] < 280


def test_long_word_failure_stays_visible_without_consuming_suffix() -> None:
    renderer = _FrameRenderer(_layout_from_plain(_PLAIN), "a" * 30 + "bbb", False)
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._centered_text",
        wraps=_centered_text,
    ) as text:
        renderer.frame(_Moment(30, "s1", None, None, 0, 0, True, 30))
    cells = [c for c in text.call_args_list if c.args[2] == "b" and c.args[1][1] < 280]
    assert len(cells) == 3
    assert all(100 < c.args[1][0] < 2100 for c in cells)
    assert all(max(ImageColor.getrgb(c.args[4])[:3]) < 100 for c in cells)


def test_single_frame_steps_preserve_loop_and_partial_failure() -> None:
    moments = list(_timeline(["q0", "q1", "q1", "q1", None], "abbx",
                             {"q0": {"a": "q1"}, "q1": {"b": "q1"}},
                             {"q0": "s0", "q1": "s1"}, 100, 1))
    assert moments[-1].state_id == "s1"
    assert moments[-1].blocked_at == 3
    assert moments[-1].step == 3


def test_many_frames_reuse_one_layout_and_write_equal_sized_images(tmp_path: Path) -> None:
    layout = _layout_from_plain(_PLAIN)
    with patch(
        "automata_extensions.fa.dfa_mixins.animation_video._layout_once",
        return_value=layout,
    ) as layout_once:
        count = write_video_frames(
            "digraph { s0 -> s1 }", ["q0", "q1"], "a", True,
            {"q0": {"a": "q1"}}, {"q0": "s0", "q1": "s1"},
            1.0, 6, tmp_path,
        )
    layout_once.assert_called_once_with("digraph { s0 -> s1 }")
    files = sorted(tmp_path.glob("frame_*.png"))
    assert len(files) == count and count > 2
    for file in files:
        with Image.open(file) as frame:
            assert frame.size == (1280, 720)
