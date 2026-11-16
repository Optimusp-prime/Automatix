"""Stable Graphviz layout and raster composition for DFA execution videos."""

from __future__ import annotations

import math
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping, Sequence

from automata.fa.fa import FAStateT
from graphviz import Source
from PIL import Image, ImageColor, ImageDraw, ImageFont


_SIZE = (1280, 720)
_SCALE = 2  # Rasterize at 2x before a Lanczos downsample.
_PAPER = "#FCFCFA"
_INK = "#303638"
_MUTED = "#9BA5A5"
_EDGE = "#A7AFAF"
_ACCENT = "#288C83"
_REJECT = "#B95850"


@dataclass(frozen=True)
class _Node:
    identifier: str
    x: float
    y: float
    rx: float
    ry: float
    label: str
    final: bool


@dataclass(frozen=True)
class _Edge:
    source: str
    target: str
    label: str | None
    points: tuple[tuple[float, float], ...]
    label_position: tuple[float, float] | None
    samples: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class _Layout:
    nodes: Mapping[str, _Node]
    edges: tuple[_Edge, ...]

    def transition(self, source: str, target: str, symbol: str) -> _Edge:
        """Find the actual labeled DFA edge, including a self-loop."""
        for edge in self.edges:
            if (edge.source, edge.target, edge.label) == (source, target, symbol):
                return edge
        raise ValueError(f"Graphviz omitted DFA transition {source}->{target}: {symbol}")


@dataclass(frozen=True)
class _Moment:
    step: int
    state_id: str
    active_symbol: int | None
    edge: tuple[str, str, str] | None
    progress: float
    pulse: float
    final: bool
    blocked_at: int | None
    phase: float = 0.0


def _ease(value: float) -> float:
    """Quintic interpolation with zero speed and acceleration at both ends."""
    t = min(1.0, max(0.0, value))
    return t * t * t * (t * (t * 6 - 15) + 10)


def _blend(foreground: str, background: str, opacity: float) -> str:
    """Flatten a translucent color onto the video's opaque background."""
    front, back = ImageColor.getrgb(foreground), ImageColor.getrgb(background)
    alpha = min(1.0, max(0.0, opacity))
    channels = [round(b + (f - b) * alpha) for f, b in zip(front[:3], back[:3])]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def _curve_samples(points: Sequence[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    """Sample Graphviz's cubic B-spline control points, including loops."""
    if len(points) < 4 or (len(points) - 1) % 3:
        return tuple(points)
    sampled: list[tuple[float, float]] = [points[0]]
    for start in range(0, len(points) - 1, 3):
        p0, p1, p2, p3 = points[start:start + 4]
        for index in range(1, 25):
            t = index / 24
            u = 1 - t
            sampled.append((
                u**3 * p0[0] + 3 * u**2 * t * p1[0]
                + 3 * u * t**2 * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * p1[1]
                + 3 * u * t**2 * p2[1] + t**3 * p3[1],
            ))
    return tuple(sampled)


def _layout_from_plain(plain: str) -> _Layout:
    """Map one Graphviz plain layout into the fixed graph panel."""
    rows = [shlex.split(line.strip()) for line in plain.splitlines() if line.strip()]
    if not rows or rows[0][0] != "graph":
        raise ValueError("Graphviz did not return a plain graph layout")
    width, height = float(rows[0][2]), float(rows[0][3])
    if width <= 0 or height <= 0:
        raise ValueError("Graphviz returned an empty graph layout")
    left, top, area_width, area_height = (85, 185, 1110, 440)
    scale = min(area_width / width, area_height / height) * _SCALE
    offset_x = (left + area_width / 2) * _SCALE - width * scale / 2
    offset_y = (top + area_height / 2) * _SCALE - height * scale / 2

    def position(x: float, y: float) -> tuple[float, float]:
        return (offset_x + x * scale, offset_y + (height - y) * scale)

    nodes: dict[str, _Node] = {}
    edges: list[_Edge] = []
    for row in rows[1:]:
        if row[0] == "node" and row[1] != "__start__":
            x, y = position(float(row[2]), float(row[3]))
            nodes[row[1]] = _Node(
                row[1], x, y, float(row[4]) * scale / 2,
                float(row[5]) * scale / 2, row[6], row[8] == "doublecircle",
            )
        elif row[0] == "edge":
            count = int(row[3])
            coordinates = tuple(
                position(float(row[index]), float(row[index + 1]))
                for index in range(4, 4 + 2 * count, 2)
            )
            remaining = row[4 + 2 * count:]
            label = remaining[0] if len(remaining) >= 5 else None
            label_position = (
                position(float(remaining[1]), float(remaining[2]))
                if label is not None else None
            )
            edges.append(_Edge(
                row[1], row[2], label, coordinates, label_position,
                _curve_samples(coordinates),
            ))
    return _Layout(nodes, tuple(edges))


def _layout_once(dot: str) -> _Layout:
    """Ask Graphviz for one immutable set of nodes and B-splines."""
    return _layout_from_plain(Source(dot).pipe(format="plain").decode("utf-8"))


def _timeline(
    trace: Sequence[FAStateT],
    word: str,
    transitions: Mapping[FAStateT, Mapping[str, FAStateT]],
    identifiers: Mapping[FAStateT, str],
    fps: float,
    render_fps: int,
) -> Iterator[_Moment]:
    """Expand each logical step into movement, arrival and rest frames."""
    initial_hold = max(1, round(render_fps * 0.4))
    final_hold = max(1, round(render_fps * 0.9))
    step_frames = max(1, round(render_fps / fps))
    last_valid = trace[0]
    blocked_at: int | None = None

    for _ in range(initial_hold):
        yield _Moment(0, identifiers[last_valid], 0 if word else None,
                      None, 0.0, 0.0, False, None)

    for index, symbol in enumerate(word):
        previous, current = trace[index:index + 2]
        paths = transitions.get(previous, {}) if previous is not None else {}
        valid = blocked_at is None and symbol in paths and paths[symbol] == current
        edge = (
            (identifiers[previous], identifiers[current], symbol)
            if valid else None
        )
        if not valid and blocked_at is None:
            blocked_at = index
        for frame in range(step_frames):
            phase = (frame + 1) / step_frames
            arrived = valid and phase >= 0.93
            state_id = identifiers[current] if arrived else identifiers[last_valid]
            active = index + 1 if arrived else index
            arrival = min(1.0, max(0.0, (phase - 0.67) / 0.33))
            yield _Moment(
                index + int(arrived), state_id,
                active if active < len(word) else None, edge,
                _ease((phase - 0.12) / 0.68),
                math.sin(math.pi * arrival) if valid else 0.0,
                False, blocked_at, phase,
            )
        if not valid:
            break
        last_valid = current

    completed = len(word) if blocked_at is None else blocked_at
    for _ in range(final_hold):
        yield _Moment(completed, identifiers[last_valid], None, None,
                      0.0, 0.0, True, blocked_at)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Use an installed sans-serif face without bundling font assets."""
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    names = (
        (str(windows / "segoeuib.ttf"), "DejaVuSans-Bold.ttf", "arialbd.ttf")
        if bold else (str(windows / "segoeui.ttf"), "DejaVuSans.ttf", "arial.ttf")
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size * _SCALE)
        except OSError:
            continue
    return ImageFont.load_default(size=size * _SCALE)


def _centered_text(
    draw: ImageDraw.ImageDraw, center: tuple[float, float], value: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont, fill: str,
) -> None:
    bounds = draw.textbbox((0, 0), value, font=font)
    draw.text((center[0] - (bounds[2] - bounds[0]) / 2,
               center[1] - (bounds[3] - bounds[1]) / 2 - bounds[1]),
              value, font=font, fill=fill)


def _status_mark(
    draw: ImageDraw.ImageDraw, center: tuple[float, float],
    color: str, *, accepted: bool, size: float,
) -> None:
    """Draw a legible check/cross without relying on font glyph coverage."""
    x, y = center
    if accepted:
        draw.line([(x - size * 0.55, y), (x - size * 0.12, y + size * 0.4),
                   (x + size * 0.65, y - size * 0.55)],
                  fill=color, width=max(2, round(size * 0.22)), joint="curve")
    else:
        draw.line([(x - size * 0.5, y - size * 0.5),
                   (x + size * 0.5, y + size * 0.5)],
                  fill=color, width=max(2, round(size * 0.22)))
        draw.line([(x + size * 0.5, y - size * 0.5),
                   (x - size * 0.5, y + size * 0.5)],
                  fill=color, width=max(2, round(size * 0.22)))


def _arrow(draw: ImageDraw.ImageDraw, samples: Sequence[tuple[float, float]], color: str) -> None:
    """Draw a small directed tip along the Graphviz spline tangent."""
    if len(samples) < 2:
        return
    x, y = samples[-1]
    px, py = samples[-2]
    angle = math.atan2(y - py, x - px)
    length = 10 * _SCALE
    wing = 5 * _SCALE
    back_x, back_y = x - length * math.cos(angle), y - length * math.sin(angle)
    draw.polygon([(x, y),
                  (back_x - wing * math.sin(angle), back_y + wing * math.cos(angle)),
                  (back_x + wing * math.sin(angle), back_y - wing * math.cos(angle))],
                 fill=color)


def _point_at(
    samples: Sequence[tuple[float, float]], fraction: float,
) -> tuple[tuple[float, float], tuple[tuple[float, float], ...]]:
    """Interpolate by traveled distance for steady motion around loops."""
    if not samples:
        raise ValueError("empty Graphviz edge spline")
    lengths = [0.0]
    for start, end in zip(samples, samples[1:]):
        lengths.append(lengths[-1] + math.dist(start, end))
    desired = lengths[-1] * min(1.0, max(0.0, fraction))
    for index in range(1, len(lengths)):
        if desired <= lengths[index]:
            segment = lengths[index] - lengths[index - 1]
            ratio = (desired - lengths[index - 1]) / segment if segment else 0.0
            start, end = samples[index - 1], samples[index]
            point = (start[0] + ratio * (end[0] - start[0]),
                     start[1] + ratio * (end[1] - start[1]))
            return point, (*samples[:index], point)
    return samples[-1], tuple(samples)


class _FrameRenderer:
    """Keep the Graphviz layout and static drawing fixed across the video."""

    def __init__(self, layout: _Layout, word: str, accepted: bool) -> None:
        self.layout = layout
        self.word = word
        self.accepted = accepted
        self.body_font = _font(21)
        self.small_font = _font(15)
        self.node_font = _font(23)
        self.badge_font = _font(20)
        self.symbol_fonts = {size: _font(size) for size in range(34, 38)}
        self.base = self._static_scene()

    def _static_scene(self) -> Image.Image:
        image = Image.new("RGB", (_SIZE[0] * _SCALE, _SIZE[1] * _SCALE), _PAPER)
        draw = ImageDraw.Draw(image)

        for edge in self.layout.edges:
            if len(edge.samples) < 2:
                continue
            draw.line(edge.samples, fill=_EDGE, width=3, joint="curve")
            _arrow(draw, edge.samples, _EDGE)
            if edge.label is not None and edge.label_position is not None:
                x, y = edge.label_position
                bounds = draw.textbbox((0, 0), edge.label, font=self.body_font)
                half_w = max(11 * _SCALE, (bounds[2] - bounds[0]) / 2 + 7 * _SCALE)
                half_h = 15 * _SCALE
                draw.rounded_rectangle((x - half_w, y - half_h,
                                        x + half_w, y + half_h),
                                       radius=8 * _SCALE, fill=_PAPER)
                _centered_text(draw, (x, y), edge.label, self.body_font, _INK)

        for node in self.layout.nodes.values():
            bounds = (node.x - node.rx, node.y - node.ry,
                      node.x + node.rx, node.y + node.ry)
            draw.ellipse(bounds, fill=_PAPER, outline=_EDGE, width=3)
            if node.final:
                inset = 5 * _SCALE
                draw.ellipse((bounds[0] + inset, bounds[1] + inset,
                              bounds[2] - inset, bounds[3] - inset),
                             outline=_EDGE, width=3)
            _centered_text(draw, (node.x, node.y), node.label,
                           self.node_font, _INK)
        return image

    def _word_strip(self, draw: ImageDraw.ImageDraw, moment: _Moment) -> None:
        if not self.word:
            _centered_text(draw, (90 * _SCALE, 81 * _SCALE),
                           "ε", self.symbol_fonts[34], _INK)
            return
        cursor = moment.active_symbol if moment.active_symbol is not None else moment.step
        if moment.blocked_at is not None:
            cursor = moment.blocked_at
        first = min(max(0, cursor - 7), max(0, len(self.word) - 18))
        visible = list(range(first, min(len(self.word), first + 18)))
        rejected = moment.blocked_at is not None or (moment.final and not self.accepted)
        rejection_start = moment.blocked_at if moment.blocked_at is not None else len(self.word) - 1
        moving_index = moment.step if moment.edge is not None and moment.phase < 0.93 else None
        fade = _ease((moment.phase - 0.68) / 0.25) if moving_index is not None else 0.0
        # One soft cursor glides to the next cell as the state emphasis transfers.
        if moment.active_symbol is not None and not rejected:
            position = float(moment.active_symbol)
            if moving_index is not None and moving_index + 1 < len(self.word):
                position = moving_index + fade
            x = (70 + (position - first) * 52) * _SCALE
            draw.rounded_rectangle((x, 56 * _SCALE, x + 40 * _SCALE, 106 * _SCALE),
                                   radius=8 * _SCALE, fill=_blend(_ACCENT, _PAPER, 0.10))
        for column, index in enumerate(visible):
            x = (70 + column * 52) * _SCALE
            opacity = 0.25 if index < moment.step else 1.0
            underline = _ACCENT if index < moment.step or index == moment.active_symbol else _EDGE
            font_size = 34
            if index == moving_index:
                opacity = 1 - 0.75 * fade
                font_size = round(34 * (1 + 0.075 * math.sin(math.pi * _ease(moment.phase / 0.5))))
            if rejected and index >= rejection_start:
                opacity, underline = 1.0, _REJECT
            ink = _blend(_INK, _PAPER, opacity)
            _centered_text(draw, (x + 20 * _SCALE, 81 * _SCALE),
                           self.word[index], self.symbol_fonts[font_size], ink)
            draw.line([(x, 114 * _SCALE), (x + 40 * _SCALE, 114 * _SCALE)],
                      fill=_blend(underline, _PAPER, opacity), width=2 * _SCALE)
        if first:
            draw.text((38 * _SCALE, 69 * _SCALE), "…",
                      font=self.body_font, fill=_MUTED)
        if visible[-1] < len(self.word) - 1:
            draw.text((1012 * _SCALE, 69 * _SCALE), "…",
                      font=self.body_font, fill=_MUTED)

    def _state_emphasis(
        self, draw: ImageDraw.ImageDraw, identifier: str, color: str, opacity: float,
    ) -> None:
        """Crossfade one state's ring/fill without covering its final-state ring."""
        if opacity <= 0:
            return
        node = self.layout.nodes[identifier]
        bounds = (node.x - node.rx, node.y - node.ry, node.x + node.rx, node.y + node.ry)
        draw.ellipse(bounds, fill=_blend(color, _PAPER, 0.10 * opacity),
                     outline=_blend(color, _EDGE, opacity), width=4)
        if node.final:
            inset = 5 * _SCALE
            draw.ellipse((bounds[0] + inset, bounds[1] + inset,
                          bounds[2] - inset, bounds[3] - inset), outline=_EDGE, width=3)
        _centered_text(draw, (node.x, node.y), node.label, self.node_font, _INK)

    def frame(self, moment: _Moment) -> Image.Image:
        """Compose one frame without asking Graphviz for a new layout."""
        image = self.base.copy()
        draw = ImageDraw.Draw(image)
        if moment.edge is not None:
            edge = self.layout.transition(*moment.edge)
            if edge.samples:
                _, covered = _point_at(edge.samples, moment.progress)
                opacity = _ease(moment.phase / 0.13) * (1 - _ease((moment.phase - 0.78) / 0.22))
                if len(covered) > 1:
                    draw.line(covered, fill=_blend(_ACCENT, _EDGE, opacity),
                              width=round((1.5 + 0.7 * opacity) * _SCALE), joint="curve")
        rejected = moment.blocked_at is not None or (moment.final and not self.accepted)
        color = _REJECT if rejected else _ACCENT
        if moment.edge is not None and moment.edge[0] != moment.edge[1]:
            fade = _ease((moment.phase - 0.68) / 0.25)
            self._state_emphasis(draw, moment.edge[0], color, 1 - fade)
            self._state_emphasis(draw, moment.edge[1], color, fade)
        else:
            self._state_emphasis(draw, moment.state_id, color, 1)
        if moment.edge is not None and moment.pulse > 0:
            node = self.layout.nodes[moment.edge[1]]
            expansion = (3 + 10 * _ease((moment.phase - 0.67) / 0.33)) * _SCALE
            draw.ellipse((node.x - node.rx - expansion, node.y - node.ry - expansion,
                          node.x + node.rx + expansion, node.y + node.ry + expansion),
                         outline=_blend(_ACCENT, _PAPER, 0.27 * moment.pulse), width=2)

        self._word_strip(draw, moment)
        if moment.final:
            badge = "Accepté" if self.accepted else "Refusé"
            foreground = _ACCENT if self.accepted else _REJECT
            _status_mark(draw, (1100 * _SCALE, 81 * _SCALE), foreground,
                         accepted=self.accepted, size=9 * _SCALE)
            _centered_text(draw, (1160 * _SCALE, 81 * _SCALE),
                           badge, self.badge_font, foreground)
        return image.resize(_SIZE, Image.Resampling.LANCZOS)


def write_video_frames(
    dot: str,
    trace: Sequence[FAStateT],
    word: str,
    accepted: bool,
    transitions: Mapping[FAStateT, Mapping[str, FAStateT]],
    identifiers: Mapping[FAStateT, str],
    fps: float,
    render_fps: int,
    folder: Path,
) -> int:
    """Render a deterministic timeline from one Graphviz layout to PNGs."""
    renderer = _FrameRenderer(_layout_once(dot), word, accepted)
    count = 0
    for count, moment in enumerate(
        _timeline(trace, word, transitions, identifiers, fps, render_fps), 1
    ):
        renderer.frame(moment).save(folder / f"frame_{count - 1:06d}.png")
    return count
