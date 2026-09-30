#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/fix_paths.py
# Description: Auto-fixes hardcoded absolute paths. SELF-CONTAINED (No external YAML required).
# Author: AI Assistant
# Date: 2026-09-30
# Version: 3.0.0 (Standalone)
# Usage: Run via GitHub Actions or locally: python tools/fix_paths.py
# =========================================

import os
import re
import sys
from pathlib import Path

# --- CONFIGURATION (Hardcoded for Simplicity) ---
REPO_NAME = "pahatid-system-project"  # CHANGE THIS IF REPO NAME CHANGES
PREFIX = f"/{REPO_NAME}"

EXTENSIONS = ['.html', '.js']
EXCLUDE_DIRS = {'.git', 'node_modules', '.github', 'vendor', 'dist', 'build', '__pycache__'}

def get_all_files(root_dir='.'):
    """Recursively finds all target files."""
    found_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in EXTENSIONS:
                full_path = os.path.join(dirpath, filename)
                found_files.append(full_path)
                
    return found_files

def fix_content(content):
    """Applies regex replacements to add PREFIX to absolute paths."""
    original = content
    
    # Rule 1: HTML Attributes (href, src, action)
    # Pattern: attr="/path" -> attr="PREFIX/path"
    def replace_attr(match):
        attr = match.group(1)
        path = match.group(2)
        # Only prefix if starts with / and doesn't already have the prefix
        if path.startswith('/') and not path.startswith(PREFIX):
            return f'{attr}="{PREFIX}{path}"'
        return match.group(0)

    content = re.sub(r'(href|src|action)="(/[^"]*)"', replace_attr, content)

    # Rule 2: JS Window Location
    # Pattern: window.location.href = '/path'
    def replace_js_href(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)
        
    content = re.sub(r"(window\.location\.href\s*=\s*['\"])(/[^'\"]+)(['\"])", replace_js_href, content)

    # Rule 3: JS Fetch
    # Pattern: fetch('/path')
    def replace_fetch(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)

    content = re.sub(r"(fetch\(['\"])(/[^'\"]+)(['\"])", replace_fetch, content)
    
    return content, (content != original)

def main():
    print(f"🚀 Starting Path Fixer... Target Prefix: '{PREFIX}'")
    
    files = get_all_files('.')
    modified_count = 0
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, was_modified = fix_content(content)
            
            if was_modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ MODIFIED: {filepath}")
                modified_count += 1
                
        except Exception as e:
            print(f"❌ ERROR processing {filepath}: {e}")
            
    print(f"\n✨ Done! Modified {modified_count} files.")
    return 0 if modified_count >= 0 else 1

if __name__ == "__main__":
    sys.exit(main())
