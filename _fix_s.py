import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
p = "sources/springer_source.py"
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()
# Delete lines 36-37 (0-indexed: 35-36) - the garbage
del lines[36]  # Greek garbage
del lines[35]  # Empty line
with open(p, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("FIXED")
