import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
with open("sources/springer_source.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '.env.")' in line and "print(" not in line:
        print("Removing line", i+1)
        del lines[i]
        break
with open("sources/springer_source.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("OK - verify with: python -m py_compile sources/springer_source.py")
