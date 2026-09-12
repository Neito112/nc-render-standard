import re

p = r"D:/Program/setup 3dsmax/Plugins/NC_Render_Standard/usermacros/NC_Render_Bridge_v1.mcr"
raw = open(p, "rb").read().decode("utf-8", errors="replace")
raw = raw.replace("\r\n", "\n")

# Cac bien body ma rollout/handler can sau khi block ket thuc -> global
SHARED = ["renderMethod", "apiKey", "gpuName", "gpuMemory", "hasCUDA",
          "coronaInstalled", "vrayInstalled", "pytorchCUDA", "pythonBin",
          "ncPluginRoot", "ncScriptsDir", "configFile"]
n = 0
for var in SHARED:
    pat = r"(^|\n)(\s+)local " + var + r" ="
    new = r"\1\2global " + var + " ="
    raw, k = re.subn(pat, new, raw, count=1)
    n += k
print("local->global vars:", n)

# Helper fns phai toan cuc de handler goi duoc sau nay
helpers = ["ncTrim", "ncStartsWith", "ncContains", "ncHas"]
decl = "".join("    global %s\n" % h for h in helpers)
anchor = "    fn ncTrim s ="
assert anchor in raw
raw = raw.replace(anchor, decl + anchor)
print("global decls for helpers: OK")

open(p, "w", encoding="utf-8", newline="\r\n").write(raw)
print("saved")
