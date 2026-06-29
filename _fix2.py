"""Simple fix for ai_manager.py"""
import os
os.chdir(r"c:\Users\Chris\Desktop\Project_Talos_v4.8.4_GitHub")

with open("core/ai_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Remove duplicate pass line after _execute_openai_compatible
content = content.replace(
    'result = self._execute_openai_compatible(prompt, response_format, provider_name)\n                    pass',
    'result = self._execute_openai_compatible(prompt, response_format, provider_name)')

# Fix 2: Remove unreachable security lines after return
content = content.replace(
    '                    return result\n                    # SECURITY: local->cloud fallback requires consent\n                    if provider_name == \'local\' and os.getenv("TALOS_ALLOW_CLOUD_FALLBACK") != "1":\n                        print("  >!> Local model failed. Cloud fallback DENIED.")\n                        return None\n                    ',
    '                    return result\n                    ')

# Fix 3: Fix VRAM detection indentation (12 spaces -> 8 spaces)
old_vram = '            vram = detect_vram_gb()\n            if vram:\n                print(f"  >> Detected {vram:.1f}GB VRAM")\n                preferred = p[\'model_name\']\n                best, _ = recommend_model(preferred)\n                if best != preferred:\n                    print(f"  >> Switching to: {best}")\n                    p[\'model_name\'] = best\n            '
new_vram = '        vram = detect_vram_gb()\n        if vram:\n            print(f"  >> Detected {vram:.1f}GB VRAM")\n            preferred = p[\'model_name\']\n            best, _ = recommend_model(preferred)\n            if best != preferred:\n                print(f"  >> Switching to: {best}")\n                p[\'model_name\'] = best\n        '
content = content.replace(old_vram, new_vram)

# Fix 4: Move VRAM block after "if not p: return" 
# First, remove it from wrong position (before if not p)
content = content.replace(
    '        vram = detect_vram_gb()\n        if vram:\n            print(f"  >> Detected {vram:.1f}GB VRAM")\n            preferred = p[\'model_name\']\n            best, _ = recommend_model(preferred)\n            if best != preferred:\n                print(f"  >> Switching to: {best}")\n                p[\'model_name\'] = best\n        \n        if not p: return',
    '        if not p: return\n        vram = detect_vram_gb()\n        if vram:\n            print(f"  >> Detected {vram:.1f}GB VRAM")\n            preferred = p[\'model_name\']\n            best, _ = recommend_model(preferred)\n            if best != preferred:\n                print(f"  >> Switching to: {best}")\n                p[\'model_name\'] = best')

with open("core/ai_manager.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixes applied")
