import functools
import collections
from typing import Any, List, Optional, Tuple, Union
from lark import Transformer, Lark, Token
from ast import literal_eval


class Path(collections.Sequence):
    __slots__ = ("parts",)

    def __init__(self, *parts: Any):
        if not self._is_valid_part(parts):
            raise ValueError(f"invalid part(s) {parts}")
        self.parts: Tuple[Any, ...] = parts

    @classmethod
    def _is_valid_part(cls, part):
        if isinstance(part, (int, float, complex, slice, str, bool)):
            return True
        if part is None:
            return True
        if isinstance(part, tuple) and all(cls._is_valid_part(p) for p in part):
            return True
        return False

    def __getitem__(self, key) -> Any:
        return self.parts[key]

    def __len__(self) -> int:
        return len(self.parts)

    @functools.cache
    def __hash__(self) -> int:
        hashable_parts = tuple(
            p if not isinstance(p, slice) else (slice, p.start, p.stop, p.step)
            for p in self.parts
        )
        return hash(hashable_parts)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Path):
            return self.parts == other.parts
        else:
            return False

    @functools.cache
    def __repr__(self) -> str:
        r = "".join([self.format_part(part) for part in self.parts])
        r = r[1:] if r and r[0] == "." else r
        return r

    @staticmethod
    def format_part(part: Any) -> str:
        if isinstance(part, str) and part.isidentifier():
            return "." + part
        elif isinstance(part, slice):
            fm = [part.start, ":", part.stop]
            if part.step is not None:
                fm += [":", part.step]
            slice_str = "".join([str(f) for f in fm if f is not None])
            return f"[{slice_str}]"
        else:
            return f"[{part!r}]"

    @classmethod
    def from_str(cls, str_path: str) -> "Path":
        tree = path_parser.parse(str_path)
        new_path = PathTransformer().transform(tree)
        return new_path


path_parser = Lark(
    start="path",
    regex=True,
    grammar=r"""
// A path is a series of dot-separated identifiers and [] based item-access.
path: [(identifier | "[" key "]") ("." identifier | "[" key "]")*]
?key: number   // item-access keys can be any hashable python literal
    | slice_key
    | boolean
    | none
    | string
    | tuple_key

tuple_key: "()"
         | "(" key ",)"
         | "(" key ("," key)+ [","] ")"

number: DEC_NUMBER
      | HEX_NUMBER
      | BIN_NUMBER
      | OCT_NUMBER
      | FLOAT_NUMBER
      | COMPLEX_NUMBER
      
?integer: DEC_NUMBER
       | HEX_NUMBER
       | BIN_NUMBER
       | OCT_NUMBER

!slice_key: [integer] ":" [integer] 
          | [integer] ":" [integer] ":" [integer]
string: /".*?(?<!\\)(\\\\)*?"/ | /'.*?(?<!\\)(\\\\)*?'/
!none: "None"
!boolean: "True" | "False"

identifier: ID_START ID_CONTINUE*
ID_START: /[\p{Lu}\p{Ll}\p{Lt}\p{Lm}\p{Lo}\p{Nl}_]+/
ID_CONTINUE: ID_START | /[\p{Mn}\p{Mc}\p{Nd}\p{Pc}·]+/

DEC_NUMBER: /-?\d+/
HEX_NUMBER: /-?0x[\da-f]*/i
OCT_NUMBER: /-?0o[0-7]*/i
BIN_NUMBER : /-?0b[0-1]*/i
FLOAT_NUMBER: /-?((\d+\.\d*|\.\d+|\d+)(e[-+]?\d+)?|\d+(e[-+]?\d+))/i
IMAG_NUMBER: (DEC_NUMBER | FLOAT_NUMBER) "j"i
COMPLEX_NUMBER: IMAG_NUMBER
              | "(" (FLOAT_NUMBER | DEC_NUMBER) /[+-]/ IMAG_NUMBER ")"
""",
)


class PathTransformer(Transformer):
    @staticmethod
    def path(args: List[Any]) -> Path:
        return Path(*args)

    @staticmethod
    def identifier(args: List[Token]) -> str:
        return str(args[0])

    @staticmethod
    def slice_key(args: List[str]) -> slice:
        sargs: List[Optional[int]] = [None, None, None]
        i = 0
        for a in args:
            if a == ":":
                i += 1
            else:
                sargs[i] = int(a) if a is not None else None
        return slice(*sargs)

    @staticmethod
    def number(args: List[str]) -> Union[int, float, complex]:
        return literal_eval(args[0])

    @staticmethod
    def none(_) -> None:
        return None

    @staticmethod
    def boolean(args: List[str]) -> bool:
        return {"True": True, "False": False}[args[0]]

    @staticmethod
    def string(args: List[str]) -> str:
        return args[0][1:-1]

    @staticmethod
    def tuple_key(args: List[Any]) -> Tuple[Any, ...]:
        return tuple(args)
