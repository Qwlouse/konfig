from hypothesis import given
import hypothesis.strategies as st

import regex
from konfig.paths import Path


# IDENTIFIER_REGEX = regex.compile(r"[\p{Lu}\p{Ll}\p{Lt}\p{Lm}\p{Lo}\p{Nl}_][\p{Lu}\p{Ll}\p{Lt}\p{Lm}\p{Lo}\p{Nl}_\p{Mn}\p{Mc}\p{Nd}\p{Pc}]*", regex.UNICODE)
# identifier failure = 'Aﷺ'

IDENTIFIER_REGEX = regex.compile(r"[^\d\W]\w*", regex.UNICODE)
identifiers = st.from_regex(IDENTIFIER_REGEX, fullmatch=True)
strings = st.text(alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Lt", "Lm", "Lo", "Nl"]), max_size=64, min_size=0)
ints = st.integers()
floats = st.floats(allow_nan=False, allow_infinity=False)
complex_numbers = st.complex_numbers(allow_infinity=False, allow_nan=False)
bools = st.booleans()
nones = st.none()
slices = st.slices(size=11)
simple_literals = strings | ints | floats | complex_numbers | bools | nones | slices


@st.composite
def random_length_tuples(draw, elements=simple_literals, min_length=0, max_length=3):
    tuple_len = draw(st.integers(min_value=min_length, max_value=max_length))
    tuple_spec = [elements] * tuple_len
    return draw(st.tuples(*tuple_spec))


literals = st.recursive(simple_literals, random_length_tuples, max_leaves=6)


@given(identifiers)
def test_python_identifier_regex(x: str):
    assert x.isidentifier()


@given(st.lists(simple_literals, min_size=1, max_size=16))
def test_path_parsing(path_elements):
    p = Path(*path_elements)
    p2 = Path.from_str(repr(p))
    assert p == p2
