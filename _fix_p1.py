#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Automated bug fixes for TALOS v4.8.1"""
import os

ROOT = r"c:\Users\Chris\Desktop\Project_Talos_v4.8.1_GitHub"
os.chdir(ROOT)

def replace_in_file(filepath, old, new, desc):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        print(f"  WARNING [{desc}]: old text not found in {filepath}")
        return False
    content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  OK [{desc}]: {filepath}")
    return True

def insert_after_def(content, func_name, guard_line):
    """Insert a guard line after a function definition."""
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        if f'def {func_name}(self)' in line:
            indent = '    ' * (len(line) - len(line.lstrip()) + 1)
            new_lines.append(indent + guard_line)
    return '\n'.join(new_lines)

# ===== B2: Add early-return guard to disabled sources =====
for src_file in ["sources/elsevier_source.py", "sources/ieee_source.py", 
                  "sources/springer_source.py", "sources/openarchives_source.py"]:
    with open(src_file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = insert_after_def(content, 'fetch_new_papers', 
                               'if not getattr(self, "enabled", True): return []')
    with open(src_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  OK [B2 guard]: {src_file}")

print("Part 1 done - B2 guards added")
