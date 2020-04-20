from ..const import get_symbols_for

unary_functions = get_symbols_for("unary_functions", "asciimath", "latex")
binary_functions = get_symbols_for("binary_functions", "asciimath", "latex")
binary_functions.pop("\\sqrt")
left_parenthesis = get_symbols_for("left_parenthesis", "asciimath", "latex")
left_parenthesis.pop(".")
left_parenthesis.pop("\\vert")
left_parenthesis.pop("[")
right_parenthesis = get_symbols_for("right_parenthesis", "asciimath", "latex")
right_parenthesis.pop(".")
right_parenthesis.pop("\\vert")
right_parenthesis.pop("]")

smb = get_symbols_for("misc_symbols", "asciimath", "latex")
smb.update(get_symbols_for("function_symbols", "asciimath", "latex"))
smb.update(get_symbols_for("colors", "asciimath", "latex"))
smb.update(get_symbols_for("relation_symbols", "asciimath", "latex"))
smb.update(get_symbols_for("logical_symbols", "asciimath", "latex"))
smb.update(get_symbols_for("operation_symbols", "asciimath", "latex"))
smb.update(get_symbols_for("greek_letters", "asciimath", "latex"))
smb.update(get_symbols_for("arrows", "asciimath", "latex"))
smb.update(left_parenthesis)
smb.update(right_parenthesis)
smb.update({"[": "[", "]": "]"})
smb = dict(sorted(smb.items(), key=lambda x: (-len(x[0]), x[0])))
