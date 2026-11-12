"""Stable Graphviz geometry and smoothly sampled DFA video moments."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

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
    assert "MOT ACCEPTÉ" in messages and "MOT REFUSÉ" in messages


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
