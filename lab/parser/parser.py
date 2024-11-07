from pathlib import Path

from lark import Lark, ParseTree


def _build_parser(grammar: Path) -> Lark:
    assert grammar.exists(), f"Grammar not found: {grammar}"
    labfile_grammar = grammar.read_text()

    return Lark(labfile_grammar, start="start", parser="lalr")


def parse(labfile: Path) -> ParseTree:
    assert labfile.exists(), f"Labfile not found: {labfile}"
    grammar = Path(__file__).parent / "labfile.lark"
    parser = _build_parser(grammar)

    return parser.parse(labfile.read_text())
