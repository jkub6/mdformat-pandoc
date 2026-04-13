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
    ("Subscript with Space", "test ~sub\\ script~ here\n", "test ~sub\\ script~ here\n"),
    ("Superscript with Space", "test ^super\\ script^ here\n", "test ^super\\ script^ here\n"),
    ("Nested Sub/Sup", "test ~sub^sup^~ here\n", "test ~sub^sup^~ here\n"),
    ("Mixed Subscript", "test ~*bold\\ sub*~ here\n", "test ~*bold\\ sub*~ here\n"),
    ("Custom Label List", "{::P} All humans are mortal.\n{::Prem2} Socrates is human.\n{::C1} Therefore, Socrates is mortal.\n", "{::P} All humans are mortal.\n{::Prem2} Socrates is human.\n{::C1} Therefore, Socrates is mortal.\n"),
    ("Custom Label with ID", "{::P(#p1)} All humans are mortal.\n", "{::P(#p1)} All humans are mortal.\n"),
    ("Tight List Validation", "1. a\n2. b\n", "1. a\n2. b\n"),
]


@pytest.mark.parametrize("name, inp, out", TEST_CASES)
def test_fmt(name, inp, out):
    assert mdformat.text(inp, extensions={"pandoc"}) == out
