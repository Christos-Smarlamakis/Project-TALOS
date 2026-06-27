import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")
with open("sources/springer_source.py", "rb") as f:
    data = f.read()
# Find the Greek garbage bytes
target = "\u0394\u03b5\u03bd \u03b2\u03c1\u03ad\u03b8\u03b7\u03ba\u03b5".encode('utf-8')
idx = data.find(target)
if idx >= 0:
    # Find end of this line (next \n after idx)
    end = data.find(b'\n', idx)
    # Delete from start of line to end of line
    start = data.rfind(b'\n', 0, idx) + 1
    data = data[:start] + data[end+1:]
    with open("sources/springer_source.py", "wb") as f:
        f.write(data)
    print("FIXED: Removed garbage line")
else:
    print("NOT FOUND")
