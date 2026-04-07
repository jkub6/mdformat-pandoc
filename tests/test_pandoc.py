import mdformat
import pytest

TEST_CASES = [
    ("Div", "::: {.c}\nTxt\n:::\n", "::: {.c}\n\nTxt\n\n:::\n"),
    ("Table", "| A |\n|---|\n| 1 |\n", "| A   |\n| --- |\n| 1   |\n"),
    ("Alpha List", "A.  test\nB.  test2\n", "A.  test\nB.  test2\n"),
    ("Roman List", "(i)  first\n(ii) second\n", "(i)  first\n(ii) second\n"),
    ("Paren List", "1)  test\n2)  test2\n", "1)  test\n2)  test2\n"),
]


@pytest.mark.parametrize("name, inp, out", TEST_CASES)
def test_fmt(name, inp, out):
    assert mdformat.text(inp, extensions={"pandoc"}) == out
