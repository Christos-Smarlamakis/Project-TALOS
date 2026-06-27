import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
for f in ["CHANGELOG_GR.md", "CHANGELOG_EN.md", "README.md", "talos.py", "core/ai_manager.py"]:
    with open(f, "r", encoding="utf-8") as fh:
        data = fh.read()
    data = data.replace("v4.8.2", "v4.8.3")
    data = data.replace("June 2026", "June 2026")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(data)
    print(f"Updated {f}")
print("Done - now commit & push")
