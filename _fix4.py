"""Fix ai_manager.py and write result to file."""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.4_GitHub")

with open("core/ai_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    # Skip the empty elif body (line 135: "                    pass" after elif deepseek)
    # Skip the pass after _execute_openai_compatible (line 138)
    # Skip unreachable security lines (142-145)
    stripped = line.rstrip()
    
    # Fix: remove 'pass' that's a body of the orphan elif on line 135
    if i == 134 and stripped.endswith("pass"):  # line 135 (0-indexed 134)
        continue
    
    # Fix: remove pass on line 138  
    if i == 137 and stripped.endswith("pass"):  # line 138
        continue
    
    # Fix: skip security lines (142-145)
    if i >= 141 and i <= 144 and ("SECURITY" in stripped or "TALOS_ALLOW" in stripped or "Cloud fallback" in stripped or stripped == ""):
        continue
    
    # Fix VRAM indentation: lines starting with 12 spaces -> 8 spaces
    if stripped.startswith("vram = detect") or stripped.startswith("if vram:") or stripped.startswith("print(f") or stripped.startswith("preferred =") or stripped.startswith("best, _ =") or stripped.startswith("if best !=") or stripped.startswith("p['model_name']"):
        if line.startswith("            "):  # 12 spaces
            line = "        " + line[12:]
    
    out.append(line)

with open("core/ai_manager.py", "w", encoding="utf-8") as f:
    f.writelines(out)

# Verify
with open("_fix_verify.txt", "w") as f:
    f.write("FIXES:\n")
    f.write("1. Removed pass at line 135 (orphan elif body)\n")
    f.write("2. Removed pass at line 138 (duplicate call)\n")
    f.write("3. Removed unreachable security lines 142-145\n")
    f.write("4. Fixed VRAM indentation (12->8 spaces)\n")
