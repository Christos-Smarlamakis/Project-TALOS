# Fix springer_source.py - remove garbage line
path = r"sources\springer_source.py"
with open(path, "rb") as f:
    data = f.read()

# The garbage line contains UTF-8 Greek bytes
# Find ".env.\")" in binary
marker = b'.env.")\r\n'
idx = data.find(marker)
if idx == -1:
    marker = b'.env.")\n'
    idx = data.find(marker)

if idx >= 0:
    # Find start of this line
    line_start = data.rfind(b'\n', 0, idx) + 1
    # Delete from line_start to idx + len(marker)
    data = data[:line_start] + data[idx + len(marker):]
    with open(path, "wb") as f:
        f.write(data)
    # Verify
    with open(path, "rb") as f:
        check = f.read()
    if b'.env.")' not in check:
        print("SUCCESS - garbage removed")
    else:
        print("FAILED - still there")
else:
    print("MARKER NOT FOUND")
    # Print surrounding bytes
    for pattern in [b'\xce\x94', b'SPRINGER', b'.env']:
        i = data.find(pattern)
        if i >= 0:
            print(f"Found {pattern!r} at byte {i}: {data[i:i+50]!r}")
