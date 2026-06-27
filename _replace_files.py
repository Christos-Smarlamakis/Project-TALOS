import os, shutil
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub")

# Delete old files
for f in ["sources/springer_source.py", "sources/openarchives_source.py"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"Deleted {f}")

# Rename new files
for old, new in [("sources/springer_new.py", "sources/springer_source.py"),
                  ("sources/openarchives_new.py", "sources/openarchives_source.py")]:
    if os.path.exists(old):
        os.rename(old, new)
        print(f"Renamed {old} -> {new}")

# Verify - check for Greek garbage
for f in [new for _, new in [("sources/springer_new.py", "sources/springer_source.py"),
                              ("sources/openarchives_new.py", "sources/openarchives_source.py")]]:
    with open(f, "r", encoding="utf-8") as fh:
        data = fh.read()
    has_greek = any(ord(c) > 127 and c not in '""''\n\r\t ' for c in data)
    if has_greek:
        print(f"WARNING: {f} still has non-ASCII characters")
    else:
        print(f"OK: {f} is clean ASCII")
