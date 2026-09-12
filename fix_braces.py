import re

path = "build_matrix/rendering_3d.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix braces for Python .format string
fix_target = """            document.getElementById('xrayToggle').addEventListener('change', (e) => {
                const isXray = e.target.checked;
                scene.traverse((child) => {
                    if (child.isMesh && child.material && child.material.name !== 'wireframe') {
                        child.material.transparent = true;
                        child.material.opacity = isXray ? 0.3 : 1.0;
                        child.material.needsUpdate = true;
                    }
                });
            });
            
            document.getElementById('sunPath').addEventListener('input', (e) => {
                const val = e.target.value / 100; // 0 to 1
                const angle = val * Math.PI; // Sunrise to sunset
                sunLight.position.set(Math.cos(angle) * 100, Math.sin(angle) * 100, 20);
            });"""

fix_replacement = """            document.getElementById('xrayToggle').addEventListener('change', (e) => {{
                const isXray = e.target.checked;
                scene.traverse((child) => {{
                    if (child.isMesh && child.material && child.material.name !== 'wireframe') {{
                        child.material.transparent = true;
                        child.material.opacity = isXray ? 0.3 : 1.0;
                        child.material.needsUpdate = true;
                    }}
                }});
            }});
            
            document.getElementById('sunPath').addEventListener('input', (e) => {{
                const val = e.target.value / 100; // 0 to 1
                const angle = val * Math.PI; // Sunrise to sunset
                sunLight.position.set(Math.cos(angle) * 100, Math.sin(angle) * 100, 20);
            }});"""

content = content.replace(fix_target, fix_replacement)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
