"""Temporary script to fix CHANGELOG version headers after bulk version bump."""
import os

ROOT = r'F:\ALEXANDRIA ECOSYSTEM\Project_TALOS\Project_Talos_v5.8.0_GitHub'

# Fix CHANGELOG_EN.md
ch_en = os.path.join(ROOT, 'CHANGELOG_EN.md')
with open(ch_en, 'r', encoding='utf-8') as f:
    content = f.read()

# Restore historical v5.7.2 entries that were incorrectly renamed
content = content.replace(
    '## [v5.8.0] - 2026-07-31 -- Constitution v2.0 Upgrade, SYNAPSE Event-Driven Protocol, 15-File Documentation Sync',
    '## [v5.7.2] - 2026-07-31 -- Constitution v2.0 Upgrade, SYNAPSE Event-Driven Protocol, 15-File Documentation Sync'
)
content = content.replace(
    '## [v5.8.0] - 2026-07-31 -- Constitution v2.0, SYNAPSE Protocol, Multi-Tier LLM Routing',
    '## [v5.7.2] - 2026-07-31 -- Constitution v2.0, SYNAPSE Protocol, Multi-Tier LLM Routing'
)

with open(ch_en, 'w', encoding='utf-8') as f:
    f.write(content)
print('CHANGELOG_EN.md: historical v5.7.2 markers restored')

# Fix CHANGELOG_GR.md
ch_gr = os.path.join(ROOT, 'CHANGELOG_GR.md')
with open(ch_gr, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '## [v5.8.0] - 2026-07-31 -- Αναβάθμιση Συντάγματος v2.0, Πρωτόκολλο SYNAPSE, Συγχρονισμός 15 Αρχείων',
    '## [v5.7.2] - 2026-07-31 -- Αναβάθμιση Συντάγματος v2.0, Πρωτόκολλο SYNAPSE, Συγχρονισμός 15 Αρχείων'
)

with open(ch_gr, 'w', encoding='utf-8') as f:
    f.write(content)
print('CHANGELOG_GR.md: historical v5.7.2 markers restored')

print('Changelog fix complete.')