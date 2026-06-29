# -*- coding: utf-8 -*-
"""
Wrapper that patches questionary to use environment variables instead of
prompt_toolkit, enabling TALOS scripts to run from subprocess without a
real console. Input is read from TALOS_GUI_STDIN env var (one line per
questionary prompt).
Usage: python _gui_runner.py <target_script> [args...]

Environment variables:
  TALOS_GUI_STDIN  — newline-separated answers for questionary prompts
  TALOS_GUI_STDIN_CONFIRM — "y" or "n" for confirm() prompts
"""
import sys
import os

# Patch questionary BEFORE any script imports it
import questionary
from questionary import prompt

# Read stdin answers from environment variable
_stdin_lines = os.environ.get("TALOS_GUI_STDIN", "").split("\n")
_stdin_idx = 0
_confirm_answer = os.environ.get("TALOS_GUI_STDIN_CONFIRM", "y").strip().lower() == "y"

def _next_line(default=""):
    """Get next line from piped stdin or env var."""
    global _stdin_idx
    if _stdin_idx < len(_stdin_lines):
        val = _stdin_lines[_stdin_idx].strip()
        _stdin_idx += 1
        return val if val else default
    return default

class _FakeResult:
    """Wraps a value to mimic questionary.Question.ask() return."""
    def __init__(self, value):
        self._value = value
    def ask(self, default=None):
        return self._value if self._value is not None else default
    def unsafe_ask(self):
        return self._value

def _fake_text(message, default="", **kwargs):
    sys.stdout.write(f"[GUI] {message}\n")
    sys.stdout.flush()
    val = _next_line(default)
    sys.stdout.write(f"[GUI] Answer: {val}\n")
    sys.stdout.flush()
    return _FakeResult(val if val else default)

def _fake_confirm(message, default=True, **kwargs):
    sys.stdout.write(f"[GUI] {message} -> {'y' if _confirm_answer else 'n'}\n")
    sys.stdout.flush()
    return _FakeResult(_confirm_answer)

def _fake_select(message, choices=None, **kwargs):
    sys.stdout.write(f"[GUI] {message}\n")
    for i, c in enumerate(choices):
        if hasattr(c, 'title') and hasattr(c, 'value'):
            sys.stdout.write(f"  {i+1}. {c.title}\n")
        elif isinstance(c, str):
            sys.stdout.write(f"  {i+1}. {c}\n")
        else:
            sys.stdout.write(f"  {i+1}. {str(c)}\n")
    sys.stdout.flush()
    # For select in GUI mode, take first non-separator choice
    for c in choices:
        if hasattr(c, 'value'):
            sys.stdout.write(f"[GUI] Auto-select: {c.title}\n")
            sys.stdout.flush()
            return _FakeResult(c.value)
        if isinstance(c, str) and not c.startswith("Back"):
            sys.stdout.write(f"[GUI] Auto-select: {c}\n")
            sys.stdout.flush()
            return _FakeResult(c.split(". ", 1)[-1] if ". " in c else c)
    return _FakeResult(None)

# Apply patches
questionary.text = _fake_text
questionary.confirm = _fake_confirm
questionary.select = _fake_select
questionary.Separator = str
questionary.Choice = lambda title, value: type('Choice', (), {'title': title, 'value': value})()

# Patch prompt_toolkit to avoid console requirement
try:
    import prompt_toolkit.output.defaults
    prompt_toolkit.output.defaults.create_output = lambda: open(os.devnull, 'w')
except Exception:
    pass

# Now run the target script
if len(sys.argv) < 2:
    print("Usage: python _gui_runner.py <target_script> [args...]")
    sys.exit(1)

target = sys.argv[1]
target_args = sys.argv[2:]

sys.argv = [target] + target_args

# CRITICAL: cd to project root (where config.json lives)
project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(target)), '..'))
os.chdir(project_root)

with open(target, encoding='utf-8') as f:
    code = compile(f.read(), target, 'exec')
exec(code, {'__name__': '__main__', '__file__': target})