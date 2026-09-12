"""Paren balance checker with a proper state machine (string/escape/comment aware)."""
import sys


def check(path):
    src = open(path, "rb").read().decode("utf-8", errors="replace")
    depth = 0
    line = 1
    min_line_depth = []  # (line, depth) when depth returns to a low value
    i = 0
    n = len(src)
    stack = []  # (line) of open parens
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        # comment: -- to end of line (only outside strings)
        if c == "-" and i + 1 < n and src[i + 1] == "-":
            while i < n and src[i] != "\n":
                i += 1
            continue
        # string literal with escapes
        if c == '"':
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                if src[i] == "\n":
                    line += 1
                i += 1
            continue
        if c == "(":
            depth += 1
            stack.append(line)
        elif c == ")":
            depth -= 1
            if stack:
                stack.pop()
        i += 1
    print(f"{path}: final depth={depth}")
    if stack:
        print("  unclosed '(' at lines:", stack[:10])
    return depth == 0


if __name__ == "__main__":
    ok = all([check(p) for p in sys.argv[1:]])
    sys.exit(0 if ok else 1)
