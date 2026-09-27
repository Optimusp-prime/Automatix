"""Portable interactive DFA animation from existing execution traces."""

from copy import deepcopy
from html.parser import HTMLParser
import json

from automata_extensions.fa import ExtendedDFA, ExtendedGNFA, ExtendedNFA
from tests.fa.test_state_elimination import _mature_dfa


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.frames: list[list[str]] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.tags.append(tag)
        values = dict(attrs)
        if "data-frames" in values:
            assert values["data-frames"] is not None
            self.frames = json.loads(values["data-frames"])


def test_mature_example_and_actual_state_progression() -> None:
    d = _mature_dfa()
    before = deepcopy(d.input_parameters)
    document = d.animate("aab")
    assert len(document) > 0
    assert type(document) is str
    assert document == d.animate("aab")
    reader = _Reader()
    reader.feed(document)
    assert {"html", "head", "body", "main", "style", "script"} <= set(reader.tags)
    assert reader.frames == [
        ["0", "", "aab"], ["1", "a", "ab"],
        ["2", "aa", "b"], ["2", "aab", ""],
    ]
    assert "Mot rejeté" in document
    assert d.input_parameters == before


def test_empty_and_accepted_words() -> None:
    d = _mature_dfa()
    empty = _Reader()
    empty.feed(d.animate(""))
    assert empty.frames == [["0", "", ""]]
    assert "Mot accepté" in d.animate("")
    accepted = _Reader()
    accepted.feed(d.animate("aaa"))
    assert accepted.frames is not None
    assert [frame[0] for frame in accepted.frames] == ["0", "1", "2", "0"]
    assert "Mot accepté" in d.animate("aaa")


def test_html_escaping_and_no_remote_assets() -> None:
    hostile = '</script><script>alert(1)</script>'
    d = ExtendedDFA(
        states={hostile}, input_symbols={"<", "&"},
        transitions={hostile: {"<": hostile, "&": hostile}},
        initial_state=hostile, final_states={hostile},
    )
    document = d.animate("<&")
    assert "&lt;/script&gt;" in document
    assert "data-frames=" in document
    assert hostile not in document
    assert "https://" not in document and "http://" not in document
    reader = _Reader()
    reader.feed(document)
    assert reader.frames is not None
    assert [frame[0] for frame in reader.frames] == [hostile] * 3


def test_animation_is_dfa_only() -> None:
    assert not hasattr(ExtendedNFA, "animate")
    assert not hasattr(ExtendedGNFA, "animate")
