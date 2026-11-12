"""Self-contained HTML animation of deterministic word reading."""

from __future__ import annotations

import html
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Protocol, cast

from automata.fa.fa import FAStateT

from automata_extensions.fa.fa_mixins.visualisation import _visual_state_ids

if TYPE_CHECKING:
    from automata_extensions.fa.dfa import ExtendedDFA


class _AnimationSource(Protocol):
    """The existing simulation methods needed by the DFA animation."""

    def execution_trace(self, word: str) -> list[FAStateT]: ...

    def accepts(self, word: str) -> bool: ...


def _state_label(state: FAStateT) -> str:
    """Give common heterogeneous immutable states a stable display form."""
    if isinstance(state, frozenset):
        return "{" + ", ".join(sorted(_state_label(item) for item in state)) + "}"
    if isinstance(state, tuple):
        return "(" + ", ".join(_state_label(item) for item in state) + ")"
    return str(state)


_HEAD = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Automatix — lecture d'un mot</title>
<style>
body { margin: 0; padding: 1.5rem; background: #10172b; color: #edf5ff;
       font: 16px/1.5 system-ui, sans-serif; }
.automatix-player { max-width: 38rem; margin: auto; padding: 1.4rem;
                    border: 1px solid #48628d; border-radius: 1rem;
                    background: #1b2845; }
.automatix-player h1 { margin: 0 0 .7rem; font-size: 1.3rem; }
.automatix-player .state { display: inline-grid; place-items: center;
                           min-width: 5rem; min-height: 5rem; margin: 1rem 0;
                           padding: .5rem; border: 2px solid #69daf4;
                           border-radius: 50%; font-weight: 700; }
.automatix-player .controls { display: flex; gap: .5rem; flex-wrap: wrap; }
.automatix-player button { padding: .5rem .8rem; border: 0; border-radius: .4rem;
                           color: #10172b; background: #8de8fa; cursor: pointer; }
.automatix-player button:disabled { opacity: .45; cursor: default; }
.automatix-player code { color: #c8b7ff; }
</style>
</head>
<body>
"""

_TAIL = """
<script>
(() => {
  const root = document.currentScript.previousElementSibling;
  const frames = JSON.parse(root.dataset.frames);
  const state = root.querySelector('[data-role="state"]');
  const progress = root.querySelector('[data-role="progress"]');
  const step = root.querySelector('[data-role="index"]');
  const previous = root.querySelector('[data-action="previous"]');
  const next = root.querySelector('[data-action="next"]');
  const play = root.querySelector('[data-action="play"]');
  let index = 0;
  let timer = null;
  function draw() {
    state.textContent = frames[index][0];
    progress.textContent = frames[index][1] + " / " + frames[index][2];
    step.textContent = String(index);
    previous.disabled = index === 0;
    next.disabled = index === frames.length - 1;
    play.disabled = frames.length < 2;
    if (next.disabled && timer !== null) {
      clearInterval(timer);
      timer = null;
      play.textContent = "Lire";
    }
  }
  previous.addEventListener("click", () => { index--; draw(); });
  next.addEventListener("click", () => { index++; draw(); });
  play.addEventListener("click", () => {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
      play.textContent = "Lire";
    } else {
      if (index === frames.length - 1) index = 0;
      play.textContent = "Pause";
      draw();
      timer = setInterval(() => { index++; draw(); }, 700);
    }
  });
  draw();
})();
</script>
</body>
</html>
"""


def _find_ffmpeg() -> str | None:
    """Find optional FFmpeg on PATH, then beside the active Python environment."""
    found = shutil.which("ffmpeg")
    if found is not None:
        return found
    environment = Path(sys.executable).parent
    candidates = (
        environment / "ffmpeg.exe",
        environment / "Scripts" / "ffmpeg.exe",
        environment / "Library" / "bin" / "ffmpeg.exe",
    ) if sys.platform.startswith("win") else (environment / "ffmpeg",)
    return next((str(path) for path in candidates if path.is_file()), None)


class AnimationMixin:
    """Animate one DFA execution as portable HTML."""

    def animate(self: _AnimationSource, word: str) -> str:
        """Build an interactive standalone HTML view of one DFA word trace.

        Reuse the verified execution_trace and accepts operations. The
        initial state is visible even without JavaScript; Previous, Next
        and Play controls reveal later states when JavaScript is available.
        All caller text is HTML-escaped or placed in an escaped JSON data
        attribute; JavaScript inserts it with textContent. The result has
        no network dependency, and the DFA is not modified. A rejected
        word still displays every configuration yielded by the trace.

        Parameters
        ----------
        word : str
            Input word, including epsilon (the empty string).

        Returns
        -------
        str
            Complete HTML document usable in a browser or HTML display.

        Raises
        ------
        Exception
            Invalid inputs and upstream simulation errors propagate.

        Complexity
        ----------
        O(T + R) time and O(R + n) space. T is the delegated DFA simulation
        cost, n is the word length and R is the generated HTML size; its
        per-frame consumed and remaining prefixes can make R = O(n**2)
        plus state-label lengths.

        References
        ----------
        Mature AnimationMixin DFA example and professor simulator goal;
        primary requirement #16 supplies state configurations.
        """
        trace = self.execution_trace(word)
        frames = [
            (_state_label(state), word[:index], word[index:])
            for index, state in enumerate(trace)
        ]
        encoded = html.escape(
            json.dumps(frames, ensure_ascii=False, separators=(",", ":")),
            quote=True,
        )
        initial = html.escape(frames[0][0])
        displayed_word = html.escape(word or "ε")
        outcome = "accepté" if self.accepts(word) else "rejeté"
        markup = (
            f'<main class="automatix-player" data-frames="{encoded}">'
            f'<h1>Lecture de <code>{displayed_word}</code></h1>'
            f'<p>Mot {outcome} · étape <span data-role="index">0</span>'
            f'/{len(trace) - 1}</p>'
            f'<output class="state" data-role="state" aria-live="polite">'
            f'{initial}</output>'
            '<p>Lu / restant : <code data-role="progress"></code></p>'
            '<div class="controls">'
            '<button type="button" data-action="previous">Précédent</button>'
            '<button type="button" data-action="next">Suivant</button>'
            '<button type="button" data-action="play">Lire</button>'
            '</div></main>'
        )
        return _HEAD + markup + _TAIL

    def export_animation_video(
        self,
        word: str,
        filename: str | Path,
        *,
        fps: float = 1.0,
        render_fps: int = 30,
    ) -> Path:
        """Export a smoothly animated DFA execution as a 1280x720 MP4.

        The verified trace and DOT source provide the logical execution and
        real graph. Graphviz computes one ``plain`` layout, including curved
        edges and self-loops. A 30-fps (by default) raster timeline moves a
        marker along each spline, highlights the active state and word
        symbol, then shows the acceptance result. ``fps`` retains its M11
        meaning of logical steps per second; ``render_fps`` is the encoded
        frame rate. An empty word has an initial hold and final result.
        A missing transition leaves the last reached state visible and
        indicates the offending symbol without adding a sink.

        Frames and the encoded H.264 MP4 are temporary until encoding
        succeeds; the existing destination is then replaced. The parent
        directory must already exist. FFmpeg is optional and looked up
        only on invocation. Neither the DFA nor HTML ``animate()`` changes.

        Parameters
        ----------
        word : str
            Word to execute, including the empty word.
        filename : str | Path
            Destination ending in .mp4, with an existing parent directory.
        fps : float, default: 1.0
            Positive, finite logical execution steps per second.
        render_fps : int, default: 30
            Positive integer encoded video frames per second. Steps faster
            than this rate cannot show multiple intermediate frames.

        Returns
        -------
        Path
            Path of the completed MP4 file.

        Raises
        ------
        ValueError
            If fps or render_fps is invalid, or the suffix is not .mp4.
        FileNotFoundError
            If the destination parent does not exist.
        RuntimeError
            If optional FFmpeg is absent, encoding fails, or no MP4 is made.
        graphviz.ExecutableNotFound
            If Graphviz dot is unavailable during frame rendering.

        Complexity
        ----------
        For n = len(word), r = render_fps and
        s = max(1, round(r / fps)), the DFA trace costs O(n).
        Graphviz lays out Q states and E edges once; its cost is external.
        At most O(r + n*s) raster frames are composed. Each frame
        copies a fixed 1280x720 canvas and may inspect at most n word
        symbols; Graphviz spline sampling is shared. FFmpeg time depends on
        frame count and content. Temporary disk space is the sum of all
        PNGs and the encoded MP4, cleaned even on failure.

        References
        ----------
        Automatix M11 and its visual redesign; primary #16 (trace) and
        #40–#41 (Graphviz); ADR-0027.
        """
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("fps must be finite and strictly positive")
        if type(render_fps) is not int or render_fps <= 0:
            raise ValueError("render_fps must be a strictly positive integer")
        output = Path(filename)
        if output.suffix.lower() != ".mp4":
            raise ValueError("video filename must end in .mp4")
        if not output.parent.is_dir():
            raise FileNotFoundError(f"destination directory does not exist: {output.parent}")
        ffmpeg = _find_ffmpeg()
        if ffmpeg is None:
            raise RuntimeError("FFmpeg is required to export an MP4 video")

        source = cast("ExtendedDFA", self)
        trace = source.execution_trace(word)
        accepted = source.accepts(word)
        ids = _visual_state_ids(source)
        base_dot = source.dot()

        with TemporaryDirectory(prefix=".automatix-video-", dir=output.parent) as folder:
            temporary = Path(folder)
            from automata_extensions.fa.dfa_mixins.animation_video import (
                write_video_frames,
            )

            frame_count = write_video_frames(
                base_dot, trace, word, accepted, source.transitions, ids,
                fps, render_fps, temporary,
            )

            encoded = temporary / "animation.mp4"
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-framerate", str(render_fps),
                "-i", str(temporary / "frame_%06d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-frames:v", str(frame_count),
                str(encoded),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError(f"FFmpeg failed to encode MP4: {result.stderr.strip()}")
            if not encoded.is_file() or encoded.stat().st_size == 0:
                raise RuntimeError("FFmpeg did not produce a nonempty MP4 file")
            encoded.replace(output)
        return output
