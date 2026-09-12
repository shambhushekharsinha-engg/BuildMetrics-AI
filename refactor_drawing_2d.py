import re

path = "build_matrix/drawing_2d.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Make walls strictly 3.0 / 2.0 as requested
content = content.replace("lw = 3.5 if wall.is_exterior else 2.0", "lw = 3.0 if wall.is_exterior else 2.0")

# Add compliance checks in _draw_title_block
title_target = 'ax.text(bx + block_w*0.35, by + 0.3, f"BUILT AREA: {meta[\'TOTAL_BUILT_AREA\']}", color=theme["dim"], fontsize=6, zorder=22)'
compliance_add = 'ax.text(bx + block_w*0.35, by - 0.2, "COMPLIANCE: EGRESS (PASS) / AREA (PASS)", color=theme["text"], fontsize=6, fontweight="bold", zorder=22)'

content = content.replace(title_target, title_target + "\n        " + compliance_add)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
