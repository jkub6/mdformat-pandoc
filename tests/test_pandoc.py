import mdformat
import pytest

TEST_CASES = [
    ("Div", "::: {.c}\nTxt\n:::\n", "::: {.c}\n\nTxt\n\n:::\n"),
    ("Table", "|A|\n|-|\n|1|\n", "| A |\n|---|\n| 1 |\n"),
]


@pytest.mark.parametrize("name, inp, out", TEST_CASES)
def test_fmt(name, inp, out):
    assert mdformat.text(inp, extensions={"pandoc"}) == out
