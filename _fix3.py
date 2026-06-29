"""Fix ai_manager.py using line-by-line approach."""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.4_GitHub")

with open("core/ai_manager.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Print lines around problem areas for debugging
print("=== LINES 133-145 (execute_request) ===")
for i in range(132, min(146, len(lines))):
    print(f"{i+1}: {repr(lines[i][:80])}")

print("\n=== LINES 217-230 (ensure_local_model) ===")
for i in range(216, min(231, len(lines))):
    print(f"{i+1}: {repr(lines[i][:80])}")
