import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
with open("sources/springer_source.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
# Remove line 37 (index 36) which contains the garbage
new_lines = []
for i, line in enumerate(lines):
    if i == 36:
        continue  # skip garbage
    new_lines.append(line)
with open("sources/springer_source.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
# Write result to file
with open("_fix_result.txt", "w") as f:
    f.write("DONE - wrote " + str(len(new_lines)) + " lines")
