# TASK: Redesign NC-Render AI Studio MaxScript rollout layout (compact dashboard)

File to edit: `usermacros/NC_Render_Bridge_v1.mcr` (in this repo root, folder `usermacros/`).
It is a 3ds Max macroScript (~1330 lines). Inside it there is ONE rollout:

```
rollout rltNCRenderPro_v1 "NC-Render AI Studio v1.0 - CUDA + API + Multi-Renderer" width:1280 height:1050
```

PROBLEM: current layout is sparse and uneven ("loãng"): left column 340px with 8 groupBoxes stacked
to y=1013, right preview 920x1016, huge gaps between sections, inconsistent margins (10/18/20),
random y positions (632, 656, 690, 700, 724...), buttons of different widths on the same row.

## YOUR JOB — layout only, zero logic changes

Rewidget the rollout so it becomes a TIGHT, PROFESSIONAL, GRID-ALIGNED dashboard:

1. New rollout size: `width:1180 height:820` (smaller, no wasted space).
2. Layout: LEFT control rail ~420px, RIGHT preview ~740px, plus a bottom status bar spanning full width.
3. Group boxes on an 8px grid, consistent internal padding (widgets start at +14/+20 from group edge),
   consistent control heights: buttons 26px, spinners/dropdowns 24px, labels 18px.
4. Two-column arrangement inside the left rail where sensible so the rail is not 8 groups tall:
   e.g. System+Update side by side; Camera / Render Method / Prompt stacked; Render buttons in one row
   (3 buttons equal width), Quality row above status bar.
5. Preview column: imageButton/preview area large (e.g. 740x560), toolbar row of preview buttons
   directly under it, prompt/editText under toolbar or move prompt editText to left rail (keep widget
   inside whichever column is more logical — KEEP ITS NAME).
6. Status label pinned bottom-left, full remaining width, height 24.
7. Vietnamese label strings: keep the TEXT exactly as-is (do not translate, do not re-encode).
8. Emoji in button labels: keep them.

## HARD RULES (violating any = broken plugin)

- Do NOT rename any widget variable (grpSystem, lblGPUInfo, btnRender1, ddlCams, spnWidth, ...).
  All `on <widget> ...` handlers and all `fn ...` definitions reference these names.
- Do NOT touch ANY line outside the rollout's widget/groupBox DECLARATION area:
  no handler bodies, no `on rltNCRenderPro_v1 open/create`, no fn definitions, no createDialog/on execute.
- Only edit: the `rollout ... width:.. height:..` line, and widget declaration lines
  (`groupBox X "..." pos:[..] width:.. height:..`, `button/label/checkbox/spinner/dropdownList/editText/
  multiedit/imageButton/listbox ... pos:[..] width:.. height:..`).
- MaxScript widget syntax: `widget_name type "caption" pos:[x,y] width:w height:h` — the caption MUST
  stay a string literal; keep `range:[...]`, `type:#float`, `labels:#(...)` etc. exactly.
- Keep widget count and set IDENTICAL (no add/remove). Only geometry (pos/width/height) may change.
- Keep one widget per line. No line continuations. ASCII-safe edits; file stays UTF-8 WITHOUT BOM,
  LF newlines. Do NOT run formatters that re-write untouched lines.
- Everything must fit: no widget may exceed the rollout bounds 1180x820; groups must not overlap.

When done, reply with a 5-line summary: column widths, each groupBox final pos/size, and confirm
"widget set unchanged: 53 declarations" (or your actual count, counted with
`grep -cE '^\s+(button|label|checkbox|editText|spinner|dropdownList|imageButton|groupBox|multiedit|listbox|radiobuttons) '`).
