path = r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub\README.md"
with open(path, "r", encoding="utf-8") as f:
    data = f.read()

# Replace all v4.8.1 references
data = data.replace("v4.8.1", "v4.8.2")
data = data.replace("May 2026", "June 2026")

with open(path, "w", encoding="utf-8") as f:
    f.write(data)
print("README updated to v4.8.2")
