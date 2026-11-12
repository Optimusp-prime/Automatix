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
from PIL import Image, ImageDraw, ImageFont


_SIZE = (1280, 720)
_SCALE = 2  # Rasterize at 2x before a Lanczos downsample.
_INK = "#223148"
_MUTED = "#7D8CA1"
_EDGE = "#AAB8C7"
_ACCENT = "#158F86"
_ACCENT_PALE = "#E4F4F0"
_REJECT = "#C45D61"
_REJECT_PALE = "#FCE9E9"


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
    left, top, area_width, area_height = (105, 158, 1070, 345)
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
    movement_frames = max(1, round(step_frames * 0.65))
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
            active: int | None
            if frame < movement_frames:
                progress = (frame + 1) / movement_frames
                state_id = identifiers[last_valid]
                pulse = 0.0
                active = index
            else:
                progress = 1.0
                state_id = identifiers[current] if valid else identifiers[last_valid]
                pulse = 1.0 - (frame - movement_frames) / max(1, step_frames - movement_frames)
                active = index + 1 if valid and index + 1 < len(word) else None
            yield _Moment(index + 1, state_id, active, edge, progress,
                          pulse if valid else 0.0, False, blocked_at)
        if not valid:
            break
        last_valid = current

    completed = len(word) if blocked_at is None else blocked_at + 1
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
        self.title_font = _font(31, bold=True)
        self.body_font = _font(18)
        self.small_font = _font(15)
        self.node_font = _font(21, bold=True)
        self.badge_font = _font(18, bold=True)
        self.base = self._static_scene()

    def _static_scene(self) -> Image.Image:
        image = Image.new("RGB", (_SIZE[0] * _SCALE, _SIZE[1] * _SCALE), "#F5F7FB")
        draw = ImageDraw.Draw(image)
        draw.text((70 * _SCALE, 37 * _SCALE), "Exécution de l'automate",
                  font=self.title_font, fill=_INK)
        draw.text((72 * _SCALE, 91 * _SCALE), "AUTOMATIX  ·  LECTURE PAS À PAS",
                  font=self.small_font, fill=_MUTED)
        draw.rounded_rectangle((59 * _SCALE, 130 * _SCALE,
                                1221 * _SCALE, 541 * _SCALE),
                               radius=22 * _SCALE, fill="white", outline="#E2E8F0",
                               width=2 * _SCALE)

        for edge in self.layout.edges:
            if len(edge.samples) < 2:
                continue
            draw.line(edge.samples, fill=_EDGE, width=2 * _SCALE, joint="curve")
            _arrow(draw, edge.samples, _EDGE)
            if edge.label is not None and edge.label_position is not None:
                x, y = edge.label_position
                bounds = draw.textbbox((0, 0), edge.label, font=self.body_font)
                half_w = max(11 * _SCALE, (bounds[2] - bounds[0]) / 2 + 7 * _SCALE)
                half_h = 15 * _SCALE
                draw.rounded_rectangle((x - half_w, y - half_h,
                                        x + half_w, y + half_h),
                                       radius=8 * _SCALE, fill="white")
                _centered_text(draw, (x, y), edge.label, self.body_font, _INK)

        for node in self.layout.nodes.values():
            bounds = (node.x - node.rx, node.y - node.ry,
                      node.x + node.rx, node.y + node.ry)
            draw.ellipse(bounds, fill="white", outline="#8799AB", width=2 * _SCALE)
            if node.final:
                inset = 5 * _SCALE
                draw.ellipse((bounds[0] + inset, bounds[1] + inset,
                              bounds[2] - inset, bounds[3] - inset),
                             outline="#8799AB", width=2 * _SCALE)
            _centered_text(draw, (node.x, node.y), node.label,
                           self.node_font, _INK)
        return image

    def _word_strip(self, draw: ImageDraw.ImageDraw, moment: _Moment) -> None:
        draw.text((73 * _SCALE, 568 * _SCALE), "MOT À LIRE",
                  font=self.small_font, fill=_MUTED)
        step = f"Étape {moment.step} / {len(self.word)}"
        bounds = draw.textbbox((0, 0), step, font=self.body_font)
        draw.text(((1206 * _SCALE) - (bounds[2] - bounds[0]), 565 * _SCALE),
                  step, font=self.body_font, fill=_MUTED)
        if not self.word:
            _centered_text(draw, (640 * _SCALE, 624 * _SCALE),
                           "ε", _font(37, bold=True), _ACCENT)
            return

        cursor = moment.active_symbol if moment.active_symbol is not None else moment.step
        first = min(max(0, cursor - 6), max(0, len(self.word) - 12))
        visible = list(range(first, min(len(self.word), first + 12)))
        chip_width, gap = 54 * _SCALE, 10 * _SCALE
        width = len(visible) * chip_width + (len(visible) - 1) * gap
        start_x = 640 * _SCALE - width / 2
        for column, index in enumerate(visible):
            x = start_x + column * (chip_width + gap)
            y = 609 * _SCALE
            if moment.blocked_at == index:
                fill, ink, border = _REJECT_PALE, _REJECT, _REJECT
            elif moment.active_symbol == index:
                fill, ink, border = _ACCENT, "white", _ACCENT
            elif index < moment.step:
                fill, ink, border = _ACCENT_PALE, "#397B72", "#CCE6DF"
            else:
                fill, ink, border = "white", _INK, "#DCE4ED"
            draw.rounded_rectangle((x, y, x + chip_width, y + 48 * _SCALE),
                                   radius=10 * _SCALE, fill=fill, outline=border,
                                   width=2 * _SCALE)
            _centered_text(draw, (x + chip_width / 2, y + 24 * _SCALE),
                           self.word[index], self.body_font, ink)
            if (index < moment.step and moment.blocked_at != index
                    and moment.active_symbol != index):
                _status_mark(draw, (x + chip_width / 2, y + 60 * _SCALE),
                             _ACCENT, accepted=True, size=6 * _SCALE)
        if first:
            draw.text((start_x - 29 * _SCALE, 616 * _SCALE), "…",
                      font=self.body_font, fill=_MUTED)
        if visible[-1] < len(self.word) - 1:
            draw.text((start_x + width + 11 * _SCALE, 616 * _SCALE), "…",
                      font=self.body_font, fill=_MUTED)

    def frame(self, moment: _Moment) -> Image.Image:
        """Compose one frame without asking Graphviz for a new layout."""
        image = self.base.copy()
        draw = ImageDraw.Draw(image)
        if moment.edge is not None:
            edge = self.layout.transition(*moment.edge)
            if edge.samples:
                marker, covered = _point_at(edge.samples, moment.progress)
                if len(covered) > 1:
                    draw.line(covered, fill=_ACCENT, width=4 * _SCALE, joint="curve")
                radius = 6 * _SCALE
                draw.ellipse((marker[0] - radius, marker[1] - radius,
                              marker[0] + radius, marker[1] + radius),
                             fill=_ACCENT, outline="white", width=2 * _SCALE)

        node = self.layout.nodes[moment.state_id]
        color = _REJECT if moment.blocked_at is not None else _ACCENT
        if moment.pulse:
            expansion = (7 + 10 * moment.pulse) * _SCALE
            draw.ellipse((node.x - node.rx - expansion,
                          node.y - node.ry - expansion,
                          node.x + node.rx + expansion,
                          node.y + node.ry + expansion),
                         outline="#BCE7DD", width=3 * _SCALE)
        draw.ellipse((node.x - node.rx - 4 * _SCALE,
                      node.y - node.ry - 4 * _SCALE,
                      node.x + node.rx + 4 * _SCALE,
                      node.y + node.ry + 4 * _SCALE),
                     outline=color, width=3 * _SCALE)

        self._word_strip(draw, moment)
        if moment.final:
            badge = "MOT ACCEPTÉ" if self.accepted else "MOT REFUSÉ"
            foreground = "#1D7659" if self.accepted else "#A7474C"
            background = "#E3F3E9" if self.accepted else _REJECT_PALE
            draw.rounded_rectangle((920 * _SCALE, 55 * _SCALE,
                                    1209 * _SCALE, 107 * _SCALE),
                                   radius=15 * _SCALE, fill=background)
            draw.ellipse((945 * _SCALE, 68 * _SCALE,
                          971 * _SCALE, 94 * _SCALE), fill=foreground)
            _status_mark(draw, (958 * _SCALE, 81 * _SCALE), "white",
                         accepted=self.accepted, size=10 * _SCALE)
            _centered_text(draw, (1090 * _SCALE, 81 * _SCALE),
                           badge, self.badge_font, foreground)
            if moment.blocked_at is not None:
                detail = f"Transition inexistante pour « {self.word[moment.blocked_at]} »"
                _centered_text(draw, (640 * _SCALE, 691 * _SCALE),
                               detail, self.small_font, _REJECT)
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
