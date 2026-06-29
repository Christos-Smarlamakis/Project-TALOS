"""Fix ai_manager.py indentation issues."""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.4_GitHub")

with open("core/ai_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Fix 1: Remove duplicate dead code (line 138 pass, lines 142-145 unreachable security check)
# Find and remove specific lines
new_lines = []
skip_next = 0
for i, line in enumerate(lines):
    if "pass" in line and "_execute_openai_compatible" in lines[i-1] if i > 0 else False:
        # This is line 138 - the pass replacing duplicate call
        continue
    if "# SECURITY: local->cloud fallback requires consent" in line:
        # Skip this and next 3 lines (142-145)
        skip_next = 3
        continue
    if skip_next > 0:
        skip_next -= 1
        continue
    new_lines.append(line)

# Fix 2: Fix VRAM code indentation (lines were at 12 spaces, need 8)
# Find "vram = detect_vram_gb()" and fix its indentation
for i, line in enumerate(new_lines):
    if "vram = detect_vram_gb()" in line:
        # Fix this and subsequent VRAM-related lines
        for j in range(i, min(i+10, len(new_lines))):
            if new_lines[j].startswith("            "):
                new_lines[j] = "        " + new_lines[j][12:]
            elif new_lines[j].strip() == "":
                break
        break

# Fix 3: Move VRAM block after "if not p: return"
# Find the lines
vram_block_start = -1
return_line = -1
for i, line in enumerate(new_lines):
    if "vram = detect_vram_gb()" in line:
        vram_block_start = i
    if vram_block_start > 0 and "if not p: return" in line:
        return_line = i
        break

if vram_block_start > 0 and return_line > 0 and vram_block_start < return_line:
    # Extract VRAM block (from vram_line to blank line before "if not p")
    vram_lines = []
    for j in range(vram_block_start, len(new_lines)):
        vram_lines.append(new_lines[j])
        if new_lines[j].strip() == "":
            break
        if "p['model_name'] = best" in new_lines[j]:
            vram_lines.append(new_lines[j+1] if j+1 < len(new_lines) else "")
            break
    
    # Remove VRAM lines from current position
    for _ in vram_lines:
        idx = -1
        for k, line in enumerate(new_lines):
            if "vram = detect_vram_gb()" in line:
                idx = k
                break
        if idx >= 0:
            new_lines.pop(idx)
    
    # Find "if not p: return" again and insert VRAM lines after it
    for i, line in enumerate(new_lines):
        if "if not p: return" in line:
            for j, vl in enumerate(vram_lines):
                new_lines.insert(i + 1 + j, vl)
            break

with open("core/ai_manager.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Fixes applied. Verify with: python -m py_compile core/ai_manager.py")
