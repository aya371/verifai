"""
Cleans up the VerifAI project structure.
- Deletes all temporary patch/fix scripts from root
- Keeps only essential files
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import os
import shutil

# ── Files to DELETE (temporary patch scripts, duplicates, debug files) ────
TO_DELETE = [
    # Root level patch/fix/debug scripts
    "add_ai_detection.py",
    "add_identity_ui.py",
    "add_multilingual.py",
    "add_platform_search.py",
    "add_theme_toggle.py",
    "apply_extractor.py",
    "apply_fixes.py",
    "claim_extractor.py",
    "debug_dates.py",
    "fact_checker.py",
    "fix_date.py",
    "fix_dates.py",
    "fix_date_normalize.py",
    "fix_indent_final.py",
    "fix_orchestrator.py",
    "fix_platform_filter.py",
    "fix_readability.py",
    "fix_source_timeline.py",
    "fix_strict_filter.py",
    "fix_tab2_final.py",
    "fix_theme_toggle.py",
    "fix_timeline_dates.py",
    "fix_websearch.py",
    "identity_modal.py",
    "identity_search_select.py",
    "integrate_auth.py",
    "patch_identity_tab.py",
    "patch_telemetry.py",
    "print_fc.py",
    "rebuild_tab2.py",
    "rebuild_tab2_v2.py",
    "rewrite_tab2_clean.py",
    "write_fact_checker.py",
    # Leftover files inside backend/agents
    "backend/agents/fix_orchestrator.py",
    "backend/agents/print_fc.py",
]

deleted, skipped = [], []
for f in TO_DELETE:
    if os.path.exists(f):
        os.remove(f)
        deleted.append(f)
    else:
        skipped.append(f)

print(f"Deleted {len(deleted)} files:")
for f in deleted:
    print(f"  ✓ {f}")

if skipped:
    print(f"\nSkipped {len(skipped)} (not found):")
    for f in skipped:
        print(f"  - {f}")

print("\nFinal structure:")
for root, dirs, files in os.walk("."):
    # Skip heavy folders
    dirs[:] = [d for d in dirs if d not in [
        ".venv", "venv", "__pycache__", ".git", "data",
        "node_modules", "site-packages"
    ]]
    level = root.replace(".", "").count(os.sep)
    indent = "  " * level
    folder = os.path.basename(root) or "verifai"
    print(f"{indent}{folder}/")
    for f in sorted(files):
        if f.endswith(".py") or f in ["requirements.txt", ".env", "README.md", ".gitignore"]:
            print(f"{indent}  {f}")

print("\nDone! Project is clean.")
