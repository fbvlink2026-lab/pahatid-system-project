#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/auto_patch_sidebar.py
# Description: AUTO-PATCHES all HTML files to use Dynamic Sidebar Loader.
#              Replaces hardcoded <ul> in sidebars with dynamic JS injection.
# Author: Pahatid System
# Date: 2026-10-08
# Version: 1.0.0
# Usage: Run from project root: python tools/auto_patch_sidebar.py
# =========================================

import os
import re
import sys
from pathlib import Path

# --- CONFIGURATION ---
TARGET_EXTENSIONS = ['.html']
EXCLUDE_DIRS = {'.git', 'node_modules', '.github', 'vendor', 'dist', 'build', '__pycache__', 'assets'} # Don't touch assets/js directly unless needed
ROOT_DIR = '.' 

# Regex Patterns for Detection and Replacement

# 1. Find the entire aside block containing the sidebar navigation list
# We look for <aside ...> ... </aside> but specifically targeting the inner <ul> that has nav links
SIDEBAR_ASIDE_PATTERN = re.compile(
    r'(<aside[^>]*class="[^"]*sidebar[^"]*"[^>]*>.*?)(<ul[^>]*>(?:\s*<li.*?</li>\s*)+</ul>)(.*?</aside>)',
    re.DOTALL | re.IGNORECASE
)

# 2. Pattern to find existing script tags to inject imports after
SCRIPT_TAG_PATTERN = re.compile(r'(<script\s+type=["\']module["\'][^>]*>)', re.IGNORECASE)

# 3. Pattern to find DOMContentLoaded or similar init functions to inject the loader call
INIT_FUNCTION_PATTERN = re.compile(r'(document\.addEventListener\(\s*[\'"]DOMContentLoaded[\'"]\s*,\s*(async\s*)?\(\)\s*=>)', re.IGNORECASE)


def get_file_role(filepath):
    """Determines user role based on directory structure."""
    path_str = str(filepath).replace('\\', '/')
    
    if '/admin/' in path_str or filepath.parent.name == 'admin':
        return 'admin'
    elif '/driver/' in path_str or filepath.parent.name == 'driver':
        return 'driver'
    elif '/commuter/' in path_str or filepath.parent.name == 'commuter':
        return 'commuter'
    else:
        return None # Skip non-role specific files (like login.html, index.html)

def process_html_file(filepath):
    """Processes a single HTML file to replace static sidebar with dynamic loader."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # STEP 1: Replace Static Sidebar <ul> with Dynamic Container
        def replace_sidebar(match):
            pre_aside = match.group(1)
            post_aside = match.group(3)
            
            # The new dynamic container
            dynamic_container = '<ul class="nav flex-column p-2" id="dynamicNavList">\n                <!-- Items injected by sidebar-loader.js -->\n            </ul>'
            
            return f"{pre_aside}{dynamic_container}{post_aside}"
        
        new_content, count = SIDEBAR_ASIDE_PATTERN.subn(replace_sidebar, content)
        
        if count > 0:
            print(f"   [SIDEBAR] Found and replaced static menu in: {filepath}")
            content = new_content
            modified = True
            
            # STEP 2: Inject Import Statement
            # Check if already imported
            if 'sidebar-loader.js' not in content:
                # Find the first module script tag
                script_match = SCRIPT_TAG_PATTERN.search(content)
                if script_match:
                    insert_pos = script_match.end()
                    import_line = "\n        import { loadDynamicSidebar } from '../assets/js/sidebar-loader.js';"
                    
                    # Adjust path depth based on location
                    # If in admin/, ../assets is correct. 
                    # If deeper, might need ../../assets. 
                    # For simplicity, assuming standard structure: /folder/file.html -> ../assets/...
                    
                    content = content[:insert_pos] + import_line + content[insert_pos:]
                    print(f"   [IMPORT] Added sidebar-loader import.")
                    modified = True

            # STEP 3: Inject Function Call inside DOMContentLoaded
            if 'loadDynamicSidebar(' not in content:
                role = get_file_role(filepath)
                if role:
                    # Find DOMContentLoaded listener
                    init_match = INIT_FUNCTION_PATTERN.search(content)
                    if init_match:
                        insert_pos = init_match.end()
                        
                        # Construct the call
                        # Note: We assume async/await pattern exists. 
                        # If not, we wrap it or just call it. 
                        # Given previous codes were async, we prepend await.
                        loader_call = f"\n            await loadDynamicSidebar('dynamicNavList', '{role}');"
                        
                        content = content[:insert_pos] + loader_call + content[insert_pos:]
                        print(f"   [CALL] Added loadDynamicSidebar('{role}') call.")
                        modified = True
                    else:
                        print(f"   [WARN] Could not find DOMContentLoaded handler in {filepath}. Skipping call injection.")
                else:
                    print(f"   [SKIP] No role detected for {filepath}. Sidebar replaced but no loader call added.")

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ ERROR processing {filepath}: {e}")
        return False

def main():
    print("🚀 Starting Auto-Patcher for Dynamic Sidebar...")
    print("-" * 50)
    
    total_files = 0
    modified_files = 0
    
    for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
        # Filter directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in TARGET_EXTENSIONS:
                full_path = Path(dirpath) / filename
                total_files += 1
                
                # Only process files that likely have a sidebar (heuristic: contains 'sidebar' class)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        head_content = f.read(2000) # Read first chunk
                    
                    if 'class="sidebar"' in head_content or 'class=\'sidebar\'' in head_content:
                         if process_html_file(full_path):
                             modified_files += 1
                except:
                    pass

    print("-" * 50)
    print(f"✨ Done! Scanned {total_files} files. Modified {modified_files} files.")
    print("\n⚠️ NEXT STEPS:")
    print("1. Ensure 'assets/js/sidebar-loader.js' exists.")
    print("2. Ensure Database table 'navigation_menu' is populated via SQL.")
    print("3. Test one Driver page and one Admin page manually.")

if __name__ == "__main__":
    sys.exit(main())
