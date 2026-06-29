"""Fix _ensure_local_model and _execute_request in ai_manager.py."""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.4_GitHub")

# Read file
path = "core/ai_manager.py"
with open(path, "rb") as f:
    data = f.read()

# =============================================
# FIX 1: Replace broken _ensure_local_method
# =============================================
# Find the method start
target = b"def _ensure_local_model(self):"
idx = data.find(target)
if idx >= 0:
    # Find method end (next "def _handle_failure")
    end_method = b"def _handle_failure"
    end_idx = data.find(end_method, idx)
    if end_idx < 0:
        end_idx = len(data)
    
    # Clean replacement method
    replacement = b"""    def _ensure_local_model(self):
        import subprocess
        p = self.providers.get('local')
        if not p: return
        try:
            resp = requests.get(f"{p['ollama_url']}/api/tags", timeout=5)
            if resp.status_code != 200:
                print("WARNING: Ollama not reachable. Local model disabled.")
                del self.providers['local']
                self.local_enabled = False
                return
            models = [m['name'] for m in resp.json().get('models', [])]
            for model_key in ['model_name', 'embedding_model']:
                m = p[model_key]
                if m not in models:
                    print(f"  >> Pulling {m}...")
                    subprocess.run(["ollama", "pull", m], check=True)
                    print(f"  >> {m} installed.")
        except Exception as e:
            print(f"WARNING: Local model setup failed: {e}.")
            if 'local' in self.providers: del self.providers['local']
            self.local_enabled = False

"""
    data = data[:idx] + replacement + data[end_idx:]
    with open(path, "wb") as f:
        f.write(data)
    print("FIX 1: _ensure_local_model replaced")

# =============================================
# FIX 2: Clean up _execute_request
# =============================================
with open(path, "rb") as f:
    data = f.read()

# Remove: "                    pass\n" after deepseek elif
data = data.replace(
    b"                    result = self._execute_deepseek_request(prompt, response_format)\n                    pass\n",
    b"                    result = self._execute_deepseek_request(prompt, response_format)\n")
# Remove: "                    pass\n" after openai_compatible
data = data.replace(
    b"                    result = self._execute_openai_compatible(prompt, response_format, provider_name)\n                    pass\n",
    b"                    result = self._execute_openai_compatible(prompt, response_format, provider_name)\n")
# Remove unreachable security lines
old_sec = b'                    return result\n                    # SECURITY'
if old_sec in data:
    # Find end of security block
    sec_start = data.find(old_sec) + len(b'                    return result\n')
    sec_end = data.find(b'                    else:', sec_start)
    if sec_end > 0:
        data = data[:sec_start] + data[sec_end:]
    else:
        data = data[:sec_start]

with open(path, "wb") as f:
    f.write(data)
print("FIX 2: _execute_request cleaned")

# Verify
with open(path, "r", encoding="utf-8") as f:
    verify = f.read()
if "vram = detect" in verify:
    print("WARNING: VRAM code still present!")
else:
    print("VRAM code removed - OK")
print("Done. Run: python -m py_compile core/ai_manager.py")
