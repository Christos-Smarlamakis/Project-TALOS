import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
with open("sources/springer_source.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
# Print all lines around the problem
for i in range(30, min(42, len(lines))):
    print(i+1, repr(lines[i][:80]))
