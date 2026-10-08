#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/pahatid_autofix.py
# Description: Self-Healing Auto-Fixer v4.0 (Fixed Blank Sidebar Logic)
# Author: Pahatid System
# Date: 2026-10-08
# Version: 4.0.0 (Strict Import Detection)
# Usage: Run via terminal or GitHub Actions: python tools/pahatid_autofix.py
# =========================================

import os
import re
import sys
from pathlib import Path

# --- CONFIGURATION ---
REPO_NAME = "pahatid-system-project"  
PREFIX = f"/{REPO_NAME}"

TARGET_DIRS = ['driver', 'admin', 'commuter'] 
FILE_EXTENSIONS = ['.html'] 
BACKUP_SUFFIX = '.bak' 

# Regex for finding <aside class="sidebar">...</aside> blocks
SIDEBAR_PATTERN = re.compile(
    r'(<aside\s+class="sidebar"[^>]*>.*?</aside>)', 
    re.DOTALL | re.IGNORECASE
)

# Regex to FIND and REMOVE the bad auto-injected script block
BAD_INJECTION_PATTERN = re.compile(
    r'\s*<!--\s*AUTO-INJECTED NAV LOADER BY pahatid_autofix\.py\s*-->\s*'
    r'<script type="module">\s*'
    r'.*?'
    r'</script>',
    re.DOTALL | re.IGNORECASE
)

# Templates for Dynamic Sidebars
DRIVER_SIDEBAR_HTML = '''        <!-- SIDEBAR NAVIGATION (Dynamic) -->
        <aside class="sidebar" id="globalSidebar">
            <div class="sidebar-header p-3 border-bottom border-dark">
                <a href="/pahatid-system-project/" class="text-decoration-none text-white fw-bold fs-5 d-block">
                    <i class="fas fa-motorcycle text-warning me-2"></i> Pahatid<span class="fw-normal ms-1">Driver</span>
                </a>
            </div>
            <ul class="nav flex-column p-2" id="dynamicNavList">
                <!-- Items loaded by sidebar-loader.js -->
            </ul>
        </aside>'''

ADMIN_SIDEBAR_HTML = '''        <!-- GLOBAL SIDEBAR NAVIGATION (Admin Context - Dynamic) -->
        <aside class="sidebar" id="globalSidebar">
            <div class="sidebar-header p-3 border-bottom border-dark">
                <a href="/pahatid-system-project/" class="text-decoration-none text-white fw-bold fs-5 d-block">
                    <i class="fas fa-shield-alt text-warning me-2"></i> Pahatid<span class="fw-normal ms-1">Admin</span>
                </a>
            </div>
            <ul class="nav flex-column p-2" id="dynamicNavList">
                <!-- Items loaded by sidebar-loader.js -->
            </ul>
        </aside>'''

COMMUTER_SIDEBAR_HTML = '''        <!-- COMMUTER SIDEBAR NAVIGATION (Dynamic) -->
        <aside class="sidebar" id="globalSidebar">
            <div class="sidebar-header p-3 border-bottom border-dark">
                <a href="/pahatid-system-project/" class="text-decoration-none text-white fw-bold fs-5 d-block">
                    <i class="fas fa-user-friends text-primary me-2"></i> Pahatid<span class="fw-normal ms-1">Commuter</span>
                </a>
            </div>
            <ul class="nav flex-column p-2" id="dynamicNavList">
                <!-- Items loaded by sidebar-loader.js -->
            </ul>
        </aside>'''

JS_INJECTION_SNIPPET = '''
    <!-- AUTO-INJECTED NAV LOADER BY pahatid_autofix.py -->
    <script type="module">
    import { loadDynamicSidebar } from '../assets/js/sidebar-loader.js';
    
    document.addEventListener('DOMContentLoaded', async () => {
        const currentPath = window.location.pathname;
        let role = 'driver'; 
        
        if (currentPath.includes('/admin/')) role = 'admin';
        else if (currentPath.includes('/commuter/')) role = 'commuter';
        
        await loadDynamicSidebar('dynamicNavList', role);
    });
    </script>
'''

def get_all_files(root_dir='.'):
    """Recursively finds all target HTML files in specified directories."""
    found_files = []
    for target in TARGET_DIRS:
        search_path = os.path.join(root_dir, target)
        if not os.path.exists(search_path):
            continue
            
        for dirpath, _, filenames in os.walk(search_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in FILE_EXTENSIONS:
                    full_path = os.path.join(dirpath, filename)
                    found_files.append(full_path)
                
    return found_files

def fix_paths(content):
    """Applies regex replacements to add PREFIX to absolute paths."""
    original = content
    
    # Rule 1: HTML Attributes (href, src, action)
    def replace_attr(match):
        attr = match.group(1)
        path = match.group(2)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f'{attr}="{PREFIX}{path}"'
        return match.group(0)

    content = re.sub(r'(href|src|action)="(/[^"]*)"', replace_attr, content)

    # Rule 2: JS Window Location
    def replace_js_href(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)
        
    content = re.sub(r"(window\.location\.href\s*=\s*['\"])(/[^'\"]+)(['\"])", replace_js_href, content)

    # Rule 3: JS Fetch
    def replace_fetch(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)

    content = re.sub(r"(fetch\(['\"])(/[^'\"]+)(['\"])", replace_fetch, content)
    
    return content, (content != original)

def has_manual_sidebar_integration(content):
    """
    CRITICAL FIX: Checks for actual JS execution capability, not just HTML structure.
    Returns True ONLY IF there is an explicit import OR function call in a script tag.
    """
    # 1. Check for explicit ES6 Import of the loader
    if re.search(r"import\s+\{\s*loadDynamicSidebar\s*\}", content):
        return True
        
    # 2. Check for direct function call inside any script block
    # We look for 'loadDynamicSidebar(' anywhere in the file, assuming it's within a script context
    # Note: This might be slightly aggressive, but safer than leaving it blank.
    if re.search(r"loadDynamicSidebar\s*\(", content):
        return True
        
    # 3. Check for the specific marker we use for manual integration in our templates
    # If developers manually added this comment, they likely handled the JS too.
    if "<!-- MANUAL SIDEBAR INTEGRATION -->" in content:
        return True

    return False

def clean_bad_injections(content):
    """Removes any previously auto-injected script blocks to prevent duplication/conflicts."""
    cleaned_content, count = BAD_INJECTION_PATTERN.subn('', content)
    if count > 0:
        print(f"   🧹 CLEANED {count} old injection(s)")
    return cleaned_content

def patch_navigation(filepath, content):
    """Replaces hardcoded sidebar with dynamic loader AND injects JS ONLY IF NECESSARY."""
    parts = Path(filepath).parts
    
    # Determine Role based on directory structure
    if 'driver' in parts:
        new_sidebar_html = DRIVER_SIDEBAR_HTML
    elif 'admin' in parts:
        new_sidebar_html = ADMIN_SIDEBAR_HTML
    elif 'commuter' in parts:
        new_sidebar_html = COMMUTER_SIDEBAR_HTML
    else:
        return content, False # Not a target file for nav patching

    # STEP 1: Clean up any existing bad injections first
    content = clean_bad_injections(content)

    # STEP 2: Check if developer has ALREADY handled the JS logic manually
    if has_manual_sidebar_integration(content):
        print(f"ℹ️  SKIP (Manual JS Integration Detected): {filepath}")
        # Even if skipped, ensure the HTML structure is correct? 
        # Usually yes, but if the HTML was already patched before, it's fine.
        # If the HTML was NOT patched but JS was manual, we should still patch HTML.
        # Let's force HTML patching even if JS is manual, just to be safe structurally.
        pass 
    
    # STEP 3: Replace Sidebar HTML Structure ALWAYS if pattern matches
    # We do this regardless of JS status because the container needs to exist for EITHER method.
    patched_content, count = SIDEBAR_PATTERN.subn(new_sidebar_html, content, count=1)
    
    html_changed = (count > 0)
    
    if not html_changed:
        # No sidebar found? Skip silently.
        return patched_content, False

    # STEP 4: Inject JS ONLY IF NO MANUAL INTEGRATION WAS DETECTED EARLIER
    # Re-check because we modified content above (though unlikely to affect JS detection)
    if not has_manual_sidebar_integration(patched_content):
        # Inject Fresh JS before </body>
        if "</body>" in patched_content:
            patched_content = patched_content.replace("</body>", f"{JS_INJECTION_SNIPPET}\n</body>")
        else:
            patched_content += JS_INJECTION_SNIPPET
        
        print(f"✅ NAV PATCHED (HTML + JS Injection): {filepath}")
        return patched_content, True
    else:
        print(f"✅ NAV PATCHED (HTML Only - JS Manual Exists): {filepath}")
        return patched_content, True # Return True because HTML changed

    return patched_content, False

def process_file(filepath):
    """Processes a single file: Fixes Paths AND Patches Navigation."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        initial_content = content
        
        # Step A: Fix Paths
        content_after_paths, paths_changed = fix_paths(content)
        
        # Step B: Patch Navigation (only if it's an HTML file)
        final_content, nav_changed = content_after_paths, False
        if filepath.endswith('.html'):
            final_content, nav_changed = patch_navigation(filepath, content_after_paths)

        # Determine if ANY change happened
        was_modified = (final_content != initial_content)

        if was_modified:
            backup_path = filepath + BACKUP_SUFFIX
            # Create backup only if it doesn't exist yet to preserve original state across runs
            if not os.path.exists(backup_path):
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    bf.write(initial_content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            status_msg = ""
            if paths_changed: status_msg += "[PATHS] "
            if nav_changed: status_msg += "[NAV] "
            print(f"💾 SAVED CHANGES ({status_msg.strip()}): {filepath}")
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ ERROR processing {filepath}: {e}")
        return False

def main():
    print("🚀 Starting Self-Healing Auto-Fixer v4.0...")
    print(f"   Target Prefix: '{PREFIX}'")
    print(f"   Scanning Directories: {TARGET_DIRS}")
    
    files = get_all_files('.')
    modified_count = 0
    error_count = 0
    
    if not files:
        print("⚠️ No files found in target directories.")
        return 0

    for filepath in files:
        try:
            if process_file(filepath):
                modified_count += 1
        except Exception as e:
            error_count += 1
            print(f"Critical Error on {filepath}: {e}")
                        
    print(f"\n✨ Done! Modified {modified_count} files. Errors encountered: {error_count}.")
    
    if modified_count > 0:
        print("💡 Tip: Review .bak files if needed, then delete them.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
