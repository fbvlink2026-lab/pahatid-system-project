#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/fix_paths.py
# Description: Automatically fixes hardcoded absolute paths to include Repo Prefix based on YAML config
# Author: AI Assistant
# Date: 2026-09-30
# Version: 2.0.0 (YAML Driven & Simple)
# Usage: Run this script from the ROOT of your project directory.
#        Command: python tools/fix_paths.py
# =========================================

import os
import re
import yaml
import sys
from pathlib import Path

def load_config():
    """Loads configuration from path_config.yaml"""
    config_path = Path("path_config.yaml")
    if not config_path.exists():
        print("❌ Error: 'path_config.yaml' not found in root directory.")
        print("   Please create it first.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error reading YAML config: {e}")
        sys.exit(1)

def get_all_files(root_dir, extensions, exclude_patterns):
    """Recursively finds all files matching extensions, excluding unwanted dirs."""
    found_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # Check exclusions
        skip = False
        for excl in exclude_patterns:
            if excl.strip('/') in dirpath.replace('\\', '/'):
                skip = True
                break
        if skip:
            continue
            
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in extensions:
                full_path = os.path.join(dirpath, filename)
                found_files.append(full_path)
                
    return found_files

def fix_file_content(content, prefix):
    """Applies replacement rules to file content."""
    original_content = content
    
    # Rule 1: HTML Attributes (href, src, action)
    # Pattern: (attr)="(/path)" -> attr="PREFIX/path"
    # We use a function for replacement to handle groups cleanly
    def replace_attr(match):
        attr = match.group(1)
        path = match.group(2)
        # Only add prefix if path starts with / and isn't already prefixed
        if path.startswith('/') and not path.startswith(prefix):
            return f'{attr}="{prefix}{path}"'
        return match.group(0)

    content = re.sub(r'(href|src|action)="(/[^"]*)"', replace_attr, content)

    # Rule 2: JS Window Location
    # Pattern: window.location.href = '/path' -> window.location.href = PREFIX'/path'
    def replace_js_href(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(prefix):
            return f"{pre}{prefix}{path}{post}"
        return match.group(0)
        
    content = re.sub(r"(window\.location\.href\s*=\s*['\"])(/[^'\"]+)(['\"])", replace_js_href, content)

    # Rule 3: JS Fetch
    # Pattern: fetch('/path') -> fetch(PREFIX'/path')
    def replace_fetch(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(prefix):
            return f"{pre}{prefix}{path}{post}"
        return match.group(0)

    content = re.sub(r"(fetch\(['\"])(/[^'\"]+)(['\"])", replace_fetch, content)
    
    return content, (content != original_content)

def main():
    print("🚀 Starting Path Fixer...\n")
    
    # 1. Load Config
    config = load_config()
    repo_name = config.get('repository_name', '')
    if not repo_name:
        print("⚠️ Warning: 'repository_name' is empty in YAML. No changes will be made.")
        return
        
    prefix = f"/{repo_name}"
    print(f"📦 Target Prefix: '{prefix}'")
    
    # 2. Get Files
    scan_dirs = config.get('scan_directories', ['.'])
    extensions = [ext.lower() for ext in config.get('extensions', ['.html', '.js'])]
    excludes = config.get('exclude_patterns', [])
    
    all_files = []
    for d in scan_dirs:
        all_files.extend(get_all_files(d, extensions, excludes))
        
    print(f"🔍 Found {len(all_files)} files to process.\n")
    
    modified_count = 0
    
    # 3. Process Each File
    for filepath in all_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, was_modified = fix_file_content(content, prefix)
            
            if was_modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ MODIFIED: {filepath}")
                modified_count += 1
            else:
                # Optional: Print skipped files if verbose needed
                pass
                
        except Exception as e:
            print(f"❌ ERROR processing {filepath}: {e}")
            
    print(f"\n✨ Done! Modified {modified_count} files.")
    print("💡 Tip: Review git diff before committing.")

if __name__ == "__main__":
    main()
