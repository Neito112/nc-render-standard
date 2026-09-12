import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, "rb").read().decode("utf-8", errors="replace").replace("\r\n", "\n")
lines = raw.split("\n")

FN_NAMES = ["updateUIForMethod", "scanMaterialsInScene", "getRenderCamera",
            "captureViewportRender", "applyResToMax", "refreshPreviewDisplay",
            "refreshCamList", "captureGhostViewport", "buildScenePrompt", "arrayToCSV"]


def strip_strings(line):
    return re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', line)


def find_block_end(lines, start):
    """fn body: tim '(' dau tien sau dau '=' o dong start (hoac dong sau),
    dem depth den khi ve 0 -> tra index dong cuoi."""
    depth = 0
    seen_open = False
    for i in range(start, len(lines)):
        s = strip_strings(lines[i])
        if not seen_open:
            # bo qua phan header den dau '='
            eq = s.find("=")
            if i == start and eq >= 0:
                s = s[eq + 1:]
            for c in s:
                if c == "(":
                    seen_open = True
                    depth = 1
                    break
            if seen_open:
                # dem tiep cac ky tu con lai cua dong nay
                rest = s[s.find("(") + 1:]
                for c in rest:
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                if depth == 0:
                    return i
                continue
        else:
            for c in s:
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
            if depth == 0:
                return i
    return None


# 1. tim va cat cac fn block
blocks = {}
for name in FN_NAMES:
    start = None
    for i, l in enumerate(lines):
        if re.match(r"^\s*fn\s+" + name + r"\s", l):
            start = i
            break
    if start is None:
        print(f"!! fn {name}: khong tim thay")
        continue
    end = find_block_end(lines, start)
    if end is None:
        print(f"!! fn {name}: khong dong duoc block")
        continue
    blocks[name] = (start, end)

print("extracted:")
for name, (s, e) in sorted(blocks.items(), key=lambda kv: kv[1][0]):
    print(f"  {name:24s} L{s+1}-{e+1} ({e-s+1} dong)")

fn_texts = {name: "\n".join(lines[s:e + 1]) for name, (s, e) in blocks.items()}

# xoa tu cuoi len
for name, (s, e) in sorted(blocks.items(), key=lambda kv: -kv[1][0]):
    del lines[s:e + 1]

# chen vao TRUOC handler dau tien trong rollout body ("on rltNCRenderPro_v1 <evt>")
# -> moi fn duoc dinh nghia truoc bat ky handler nao goi no, van giu rollout scope
anchor = None
for i, l in enumerate(lines):
    if re.match(r"^\s*on rltNCRenderPro_v1\s+\w+\s+do", l):
        anchor = i
        break
assert anchor is not None, "first handler not found"

insert = ["", "        -- ===== HELPERS hoisted TRUOC handler dau tien: fn phai duoc dinh nghia",
          "        --        truoc khi on open/pressed chay (clause order = execution order) ====="]
for name in FN_NAMES:
    if name in fn_texts:
        insert.append("")
        insert.append(fn_texts[name])

lines = lines[:anchor] + insert + lines[anchor:]
out = "\n".join(lines)
open(p, "w", encoding="utf-8", newline="\r\n").write(out)

# verify
vlines = out.split("\n")
first_open = min(i for i, l in enumerate(vlines, 1) if re.match(r"\s*on rltNCRenderPro_v1 open", l))
first_handler = min(i for i, l in enumerate(vlines, 1) if re.match(r"\s*on rltNCRenderPro_v1\s+\w+\s+do", l))
allok = True
for name in FN_NAMES:
    fni = [i for i, l in enumerate(vlines, 1) if re.match(r"^\s*fn\s+" + name + r"\s", l)]
    ok = len(fni) == 1 and fni[0] < first_handler
    allok &= ok
    print(f"  {name:24s} L{fni[0] if fni else -1:5d} < first-handler L{first_handler}: {ok}{'  DUP!' if len(fni)>1 else ''}")
print("RESULT:", "OK" if allok else "BROKEN")
