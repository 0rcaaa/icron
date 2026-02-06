#!/usr/bin/env python3
"""
Rename a Python project throughout the codebase.

Usage:
    python rename_project.py <old_name> <new_name> [--dry-run]

Example:
    python rename_project.py nanobot icron
    python rename_project.py nanobot icron --dry-run
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Set


def color(text: str, code: str) -> str:
    """Add ANSI color codes."""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
        "red": "\033[91m",
        "gray": "\033[90m",
        "reset": "\033[0m",
    }
    return f"{colors.get(code, '')}{text}{colors['reset']}"


def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    skip_patterns = {
        ".git", "__pycache__", "node_modules", ".egg-info",
        ".pytest_cache", ".venv", "venv", ".tox", "dist", "build"
    }
    parts = set(path.parts)
    return bool(parts & skip_patterns)


def update_file_content(filepath: Path, replacements: Dict[str, str], dry_run: bool = False) -> bool:
    """Update content in a file with given replacements."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False
    
    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    if content != original:
        if not dry_run:
            filepath.write_text(content, encoding="utf-8")
        return True
    return False


def rename_project(
    project_path: Path,
    old_name: str,
    new_name: str,
    dry_run: bool = False
) -> None:
    """Perform comprehensive project rename."""
    
    old_upper = old_name.upper()
    new_upper = new_name.upper()
    
    print(f"\n{'=' * 50}")
    print(color("  Project Rename Script", "cyan"))
    print(f"{'=' * 50}")
    print(f"  From: {color(old_name, 'yellow')}")
    print(f"  To:   {color(new_name, 'green')}")
    print(f"  Path: {color(str(project_path), 'gray')}")
    if dry_run:
        print(color("  Mode: DRY RUN (no changes will be made)", "magenta"))
    print(f"{'=' * 50}\n")
    
    # Replacements for Python files
    python_replacements = {
        f"from {old_name}.": f"from {new_name}.",
        f"import {old_name}": f"import {new_name}",
        f".{old_name}/": f".{new_name}/",
        f".{old_name}\"": f".{new_name}\"",
        f"~/.{old_name}": f"~/.{new_name}",
        f"{old_upper}_": f"{new_upper}_",
        f"\"{old_name}\"": f"\"{new_name}\"",
        f"'{old_name}'": f"'{new_name}'",
        f"{old_name} - ": f"{new_name} - ",
        f"{old_name} v": f"{new_name} v",
        f"# {old_name}": f"# {new_name}",
        f"for {old_name}": f"for {new_name}",
        f"of {old_name}": f"of {new_name}",
        f"is {old_name}": f"is {new_name}",
        f"I am {old_name}": f"I am {new_name}",
    }
    
    # Replacements for config files
    config_replacements = {
        **python_replacements,
        f'name = "{old_name}-ai"': f'name = "{new_name}"',
        f'name = "{old_name}"': f'name = "{new_name}"',
        f'{old_name} = "{old_name}': f'{new_name} = "{new_name}',
        f'packages = ["{old_name}"]': f'packages = ["{new_name}"]',
        f'"{old_name}" = "{old_name}"': f'"{new_name}" = "{new_name}"',
        f"{old_name}/": f"{new_name}/",
        f"{old_name}/**": f"{new_name}/**",
        f"{old_name} contributors": f"{new_name} contributors",
        f"pip install {old_name}": f"pip install {new_name}",
    }
    
    # Documentation replacements
    doc_replacements = {
        old_name: new_name,
        f"zebbern/{new_name}": f"zebbern/{new_name}",  # GitHub URL update
        f"{old_upper}_": f"{new_upper}_",
        f".{old_name}": f".{new_name}",
    }
    
    # Step 1: Rename package folder
    print(color("Step 1: Renaming package folder...", "yellow"))
    old_folder = project_path / old_name
    new_folder = project_path / new_name
    
    if old_folder.exists():
        if new_folder.exists():
            print(color(f"  [Warning] Target folder already exists: {new_name}", "yellow"))
        else:
            if not dry_run:
                old_folder.rename(new_folder)
            print(color(f"  [Renamed] {old_name}/ -> {new_name}/", "green"))
    else:
        print(color(f"  [Skip] Folder '{old_name}' not found", "gray"))
    
    # Step 2: Update Python files
    print(color("\nStep 2: Updating Python files...", "yellow"))
    py_count = 0
    for py_file in project_path.rglob("*.py"):
        if should_skip_path(py_file):
            continue
        if update_file_content(py_file, python_replacements, dry_run):
            rel_path = py_file.relative_to(project_path)
            print(color(f"  [Updated] {rel_path}", "green"))
            py_count += 1
    print(color(f"  [Done] Updated {py_count} Python files", "cyan"))
    
    # Step 3: Update config files
    print(color("\nStep 3: Updating configuration files...", "yellow"))
    config_files = [
        "pyproject.toml", "setup.py", "setup.cfg",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml"
    ]
    for config_file in config_files:
        filepath = project_path / config_file
        if filepath.exists():
            if update_file_content(filepath, config_replacements, dry_run):
                print(color(f"  [Updated] {config_file}", "green"))
    
    # Step 4: Update documentation
    print(color("\nStep 4: Updating documentation...", "yellow"))
    md_count = 0
    for ext in ["*.md", "*.rst", "*.txt"]:
        for doc_file in project_path.rglob(ext):
            if should_skip_path(doc_file):
                continue
            if update_file_content(doc_file, doc_replacements, dry_run):
                rel_path = doc_file.relative_to(project_path)
                print(color(f"  [Updated] {rel_path}", "green"))
                md_count += 1
    print(color(f"  [Done] Updated {md_count} documentation files", "cyan"))
    
    # Step 5: Update environment files
    print(color("\nStep 5: Updating environment files...", "yellow"))
    env_files = [".env", ".env.example", ".env.local", ".env.development"]
    env_replacements = {
        f"{old_upper}_": f"{new_upper}_",
        old_name: new_name,
    }
    for env_file in env_files:
        filepath = project_path / env_file
        if filepath.exists():
            if update_file_content(filepath, env_replacements, dry_run):
                print(color(f"  [Updated] {env_file}", "green"))
    
    # Summary
    print(f"\n{'=' * 50}")
    print(color("  Rename Complete!", "green"))
    print(f"{'=' * 50}")
    
    if dry_run:
        print(color("\n[DRY RUN] No changes were made.", "magenta"))
        print("Run without --dry-run to apply changes.")
    else:
        print(color("\nNext steps:", "yellow"))
        print(color(f"  1. Reinstall: pip install -e .", "gray"))
        print(color(f"  2. Test: python -m {new_name} --version", "gray"))
        print(color(f"  3. Commit: git add -A && git commit -m 'Rename {old_name} to {new_name}'", "gray"))
    
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    dry_run = "--dry-run" in sys.argv
    
    project_path = Path.cwd()
    
    rename_project(project_path, old_name, new_name, dry_run)


if __name__ == "__main__":
    main()
