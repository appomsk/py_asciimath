from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
import re
import socket

# # from future import standard_library

# # standard_library.install_aliases()
try:
    import http.client as httplib
except ImportError:
    import httplib

try:
    import collections.abc as collections
except ImportError:
    import collections

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


def alias_string(mapping, init=False, alias=True, prefix=""):
    mapping = list(mapping.items())
    s = (
        "|"
        if init
        else ""
        + mapping[0][0]
        + (
            " -> " + (prefix + "_" if prefix != "" else "") + mapping[0][1]
            if alias
            else ""
        )
    )
    for k, v in mapping[1:]:
        s = (
            s
            + "\n\t| "
            + k
            + (
                " -> " + (prefix + "_" if prefix != "" else "") + v
                if alias
                else ""
            )
        )
    return s


def check_connection(url="www.google.com", timeout=10):
    conn = httplib.HTTPSConnection(url, timeout=timeout)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except (httplib.HTTPException, socket.error):
        conn.close()
        return False


def encapsulate_mrow(s):
    return "<mrow>" + s + "</mrow>"


def concat(s):
    return '"' + s + '"'


def flatten(l):  # pragma: no cover
    """Flatten a list (or other iterable) recursively"""
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, str):
            for sub in flatten(el):
                yield sub
        else:
            yield el


class UtilsMat(object):
    """Static class to check matrix-structure of a string and returns its
    LaTeX translation.

    It performs two opertions:
    1) Given a string, it checks if the string could be a rendered as LaTeX
       matrix. A correct matrix structure is:
       L [... (, ...)*], [... (, ...)*] (, [... (, ...)*])* R or
       L (... (, ...)*), (... (, ...)*) (, (... (, ...)*))* R, where L and R
       are all the possible left and right parenthesis defined by the parser;
       '[... (, ...)*]' or '(... (, ...)*)' identifies a row in the matrix
       which can be made by one or more columns, comma separated.
       In order to be considered as a matrix, the string must contain at
       leat two rows and every rows must contain the same number of columns
    2) Given a correctly matrix-like string, it returns the LaTeX translation:
       col (& col)* \\\\ col (& col)* (\\\\ col (& col)*)*
    """

    left_par = ["(", "(:", "[", "{", "{:", "|:", "||:", "langle", "&langle;"]
    right_par = [")", ":)", "]", "}", ":}", ":|", ":||", "rangle", "&rangle;"]
    mathml_par_pattern = re.compile(
        r"<mo>"
        r"(\,|\(|\(:|\[|\{|\{:|\|:|\|\|:|&langle;|"
        r"\)|:\)|\]|\}|:\}|:\||:\|\||&rangle;)"
        r"</mo>",
    )

    @classmethod
    def is_par(cls, c):
        return c in cls.left_par or c in cls.right_par

    @classmethod
    def get_row_par(cls, s):
        """Given a string, it returns the first index i such that the char in
        position i of the string is a left parenthesis, '(' or '[', and the
        open-close parenthesis couple, needed to identify matrix
        rows in the string.

        Parameters:
        - s: str

        Return:
        - i: int, [left_par, right_par]: list
        """

        for i, c in enumerate(s):
            if c == "[" or c == "(":
                return i, ["[", "]"] if c == "[" else ["(", ")"]
        return -1, []

    @classmethod
    def check_mat(cls, s, olang="mathml"):
        """Given a string, runs a matrix-structure check.
        Return True if the string s has a matrix-structure-like,
        False otherwise. It returns also the row delimiters.

        Parameters:
        - s: str

        Return:
        - b: bool
        - [l_par, r_par]: list
        """

        if olang == "mathml":
            s = re.sub(
                cls.mathml_par_pattern,
                lambda match: match.group(1)
                if match.group(1) != "&langle;"
                and match.group(1) != "&rangle;"
                else (
                    "("
                    if match.group(1) == "&langle;"
                    or match.group(1) == "|:"
                    or match.group(1) == "||:"
                    else ")"
                ),
                s,
            )
        rows = 0
        cols = 0
        max_cols = 0
        par_stack = []
        transitions = 0
        i, row_par = cls.get_row_par(s)
        if i != -1 or row_par == []:
            for c in s[i:]:
                # c is a left par
                if c in cls.left_par:
                    if transitions != rows:
                        logging.info("ROW WITHOUT COMMA")
                        return False, []
                    par_stack.append(c)
                # c is a right par
                elif c in cls.right_par:
                    if len(par_stack) == 0:
                        logging.info("UNMATCHED PARS")
                        return False, []
                    else:
                        par_stack.pop()
                    if len(par_stack) == 0:
                        transitions = transitions + 1
                        if transitions == 1 and max_cols == 0 and cols > 0:
                            max_cols = cols
                        elif max_cols != cols:
                            logging.info("COLS DIFFER")
                            return False, []
                        cols = 0
                elif c == ",":
                    if len(par_stack) == 1 and par_stack[-1] == row_par[0]:
                        cols = cols + 1
                    elif len(par_stack) == 0:
                        # If the comma is not at the and of the string
                        # count another row
                        rows = rows + 1
                        if transitions - rows != 0:
                            logging.info(
                                "NO OPEN-CLOSE PAR BETWEEN TWO COMMAS"
                            )
                            return False, []
            if len(par_stack) != 0:
                logging.info("UNMATCHED PARS")
                return False, []
            elif rows == 0 or transitions - rows > 1:
                logging.info("MISSING COMMA OR EMPTY ROW")
                return False, []
            return True, row_par
        else:
            return False, []

    @classmethod
    def get_latex_mat(cls, s, row_par=["[", "]"]):
        """Given a known matrix-structured string, translate it into the
        matrix LaTeX format.

        Parameters:
        - s: str
        - max_cols: int. How many columns per rows
        - row_par: list. Row delimiters

        Return:
        - mat: str
        """

        def is_empty_col(s):
            for c in s[::-1]:
                if c == "&" or c == "\\":
                    return True
                elif not c.isspace():
                    return False
            return True

        empty_col = True
        stack_par = []
        mat = ""
        if row_par != []:
            for i, c in enumerate(s):
                if c == row_par[0]:
                    stack_par.append(c)
                    if len(stack_par) > 1:
                        mat = mat + c
                elif c == row_par[1]:
                    stack_par.pop()
                    if len(stack_par) > 0:
                        mat = mat + c
                    else:
                        # Remove '\\right' from the last parenthesis
                        mat = mat[: len(mat) - 6]
                        # Need to go backward after \\right removal
                        # and check if col is empty
                        if is_empty_col(mat):
                            mat = mat + "\\null"
                        empty_col = True
                elif c == "," and len(stack_par) == 1:
                    mat = mat + (" & " if not empty_col else "\\null & ")
                elif c == "," and len(stack_par) == 0:
                    mat = mat + " \\\\ "
                else:
                    # Does not include \\left in the result string
                    if len(stack_par) > 0:
                        if not c.isspace():
                            empty_col = False
                        mat = mat + c
            return mat
        else:
            return s

    @classmethod
    def get_mathml_mat(cls, s, row_par=["[", "]"]):
        """Given a known matrix-structured string, translate it into the
        matrix LaTeX format.

        Parameters:
        - s: str
        - row_par: list. Row delimiters

        Return:
        - mat: str
        """

        split = re.split(cls.mathml_par_pattern, s,)
        stack_par = []
        mat = ""
        if row_par != []:
            for i, c in enumerate(split):
                if c == row_par[0]:
                    stack_par.append(c)
                    if len(stack_par) == 1:
                        mat = mat + "<mtr><mtd>"
                    elif len(stack_par) > 1:
                        mat = mat + "<mo>" + c + "</mo>"
                elif c in cls.left_par:
                    stack_par.append(c)
                    mat = mat + "<mo>" + c + "</mo>"
                elif c == row_par[1]:
                    stack_par.pop()
                    if len(stack_par) > 0:
                        mat = mat + "<mo>" + c + "</mo>"
                    else:
                        mat = (
                            mat
                            + "</mtd>"
                            + ("</mtr>" if i == len(split) - 2 else "")
                        )
                elif c in cls.right_par:
                    stack_par.pop()
                    mat = mat + "<mo>" + c + "</mo>"
                elif c == ",":
                    if len(stack_par) == 1:
                        mat = mat + "</mtd><mtd>"
                    elif len(stack_par) == 0:
                        mat = mat + "</mtr>"
                    else:
                        mat = mat + "<mo>" + c + "</mo>"
                # Initial and ending <mrow></mrow> are not needed if this is a matrix
                elif (c == "<mrow>" or c == "</mrow>") and len(stack_par) == 0:
                    pass
                elif c != "":
                    if len(stack_par) == 1 and stack_par[-1] == row_par[0]:
                        if (
                            split[i - 1] == row_par[0]
                            and split[i + 1] == row_par[1]
                        ):
                            # Discard unneeded <mrow> tag
                            mat = mat + c[6 : len(c) - 7]
                        elif split[i - 1] == row_par[0]:
                            # Discard unneeded <mrow> tag
                            mat = mat + c[6:]
                        elif split[i + 1] == row_par[1]:
                            # Discard unneeded </mrow> tag
                            mat = mat + c[: len(c) - 7]
                        else:
                            mat = mat + c
                    else:
                        mat = mat + c
            return mat
        else:
            return s


if __name__ == "__main__":
    s = "<mo>[</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>]</mo><mo>,</mo><mo>[</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>]</mo>"
    print(UtilsMat.get_mat(s))
