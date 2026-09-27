"""Self-contained HTML animation of deterministic word reading."""

from __future__ import annotations

import html
import json
from typing import Protocol

from automata.fa.fa import FAStateT


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
