from pathlib import Path
from lab.parser.parser import parse


def test_parse_should_generate_valid_tree():
    labfile = Path(__file__).parent / "Labfile.test"
    tree = parse(labfile)
    print(tree.pretty())
    print(tree)
