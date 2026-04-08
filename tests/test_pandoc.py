import mdformat
import pytest

TEST_CASES = [
    ("Div", "::: {.c}\nTxt\n:::\n", "::: {.c}\n\nTxt\n\n:::\n"),
    ("Table", "| A |\n|---|\n| 1 |\n", "| A   |\n| --- |\n| 1   |\n"),
    ("Alpha List", "A.  test\nB.  test2\n", "A.  test\nB.  test2\n"),
    ("Roman List", "(i)  first\n(ii) second\n", "(i)  first\n(ii) second\n"),
    ("Paren List", "1)  test\n2)  test2\n", "1)  test\n2)  test2\n"),
    ("Alpha Ambiguity", "A.  test\nB.  test2\nC.  test3\n", "A.  test\nB.  test2\nC.  test3\n"),
    ("Example List", "(@one) test\n(@two) test2\n", "(@one) test\n(@two) test2\n"),
    ("Subscript", "test ~sub~ here\n", "test ~sub~ here\n"),
    ("Superscript", "test ^super^ here\n", "test ^super^ here\n"),
    ("Footnote Block", "test[^1]\n\n[^1]: \n    note\n", "test[^1]\n\n[^1]: \n    note\n"),
    ("Inline Footnote", "test ^[inline footnote]\n", "test ^[inline footnote]\n"),
    ("Bullet List", "- a\n- b\n", "- a\n- b\n"),
]


@pytest.mark.parametrize("name, inp, out", TEST_CASES)
def test_fmt(name, inp, out):
    assert mdformat.text(inp, extensions={"pandoc"}) == out
