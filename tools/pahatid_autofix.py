#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/pahatid_autofix.py
# Description: Master Auto-Fixer v8.2 (Delete Existing Layout CSS & Re-Inject)
# Author: AI Assistant
# Date: 2026-10-09
# Version: 8.2.0 (Aggressive Cleanup for Guaranteed Consistency)
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

# Regex to FIND and REMOVE our OWN previous injections
OUR_PREVIOUS_INJECTION_PATTERN = re.compile(
    r'\s*<!--\s*AUTO-INJECTED MANDATORY LAYOUT CORE BY pahatid_autofix\.py\s*-->\s*'
    r'<style>\s*'
    r'.*?'
    r'</style>',
    re.DOTALL | re.IGNORECASE
)

# Regex to FIND and REMOVE EXTERNAL/MANUAL style blocks that contain core layout keywords
# This is the aggressive cleaner. It looks for <style> tags containing .sidebar, .app-wrapper, etc.
MANUAL_LAYOUT_STYLE_PATTERN = re.compile(
    r'<style[^>]*>\s*'
    r'(?:[^\n]*?(?:\.sidebar|\.app-wrapper|\.mobile-menu-toggle|\.main-content)[^\n]*?\s*\{[^\}]*?\}\s*)+' # Simple heuristic for presence
    r'.*?'
    r'</style>',
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

# THE MANDATORY LAYOUT CORE (The New Standard)
MASTER_SIDEBAR_CSS = '''
    <!-- AUTO-INJECTED MANDATORY LAYOUT CORE BY pahatid_autofix.py -->
    <style>
        /* =========================================
           PAHATID SYSTEM - MANDATORY LAYOUT CORE
           Version: 3.7.0 (Final Stable Release)
           Description: Unified Sidebar, Hamburger & Document Flow Logic
           ========================================= */

        /* --- 1. GLOBAL RESETS & BODY FLOW --- */
        body, html {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Roboto, sans-serif;
            background-color: #f4f6f9;
            overflow-x: hidden; 
            height: auto; 
        }

        /* --- 2. THE APP WRAPPER (Flex Container) --- */
        .app-wrapper {
            display: flex;
            width: 100%;
            min-height: 100vh; 
            position: relative;
            align-items: flex-start; 
        }

        /* --- 3. SIDEBAR BEHAVIOR --- */
        .sidebar {
            width: 260px;
            background: #212529;
            color: white;
            position: sticky; 
            top: 0;
            height: 100vh; 
            z-index: 1000;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s ease-in-out;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            overflow-y: auto; 
            flex-shrink: 0;
        }

        /* --- 4. MAIN CONTENT AREA --- */
        .main-content {
            flex-grow: 1;
            width: calc(100% - 260px); 
            position: relative;
            background: #f4f6f9;
            min-height: 100vh;
        }

        /* --- 5. HAMBURGER BUTTON (PERSISTENT OVERLAY) --- */
        .mobile-menu-toggle {
            display: none; 
            position: fixed !important; 
            top: 15px;
            left: 15px;
            z-index: 9999; 
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--pahatid-primary, #0d6efd);
            color: white;
            border: none;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            cursor: pointer;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: transform 0.2s;
        }
        .mobile-menu-toggle:active { transform: scale(0.9); }

        /* --- 6. SIDEBAR OVERLAY (MOBILE BACKDROP) --- */
        .sidebar-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 998; 
            opacity: 0;
            transition: opacity 0.3s;
            backdrop-filter: blur(2px);
        }
        .sidebar-overlay.active {
            display: block;
            opacity: 1;
        }

        /* --- 7. MOBILE RESPONSIVENESS (< 992px) --- */
        @media (max-width: 991.98px) {
            
            .app-wrapper {
                display: block; 
            }

            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100dvh; 
                width: min(280px, 85vw); 
                transform: translateX(-100%); 
                box-shadow: none;
                z-index: 1000;
                overflow-y: auto;
            }
            
            .sidebar.open {
                transform: translateX(0);
                box-shadow: 5px 0 15px rgba(0,0,0,0.2);
            }

            .main-content {
                width: 100%;
                margin-left: 0;
            }

            .mobile-menu-toggle {
                display: flex !important; 
            }

            .page-title-row, 
            header.main-header:first-child {
                padding-left: 60px !important; 
            }
        }
    </style>
'''

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
    
    def replace_attr(match):
        attr = match.group(1)
        path = match.group(2)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f'{attr}="{PREFIX}{path}"'
        return match.group(0)

    content = re.sub(r'(href|src|action)="(/[^"]*)"', replace_attr, content)

    def replace_js_href(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)
        
    content = re.sub(r"(window\.location\.href\s*=\s*['\"])(/[^'\"]+)(['\"])", replace_js_href, content)

    def replace_fetch(match):
        pre = match.group(1)
        path = match.group(2)
        post = match.group(3)
        if path.startswith('/') and not path.startswith(PREFIX):
            return f"{pre}{PREFIX}{path}{post}"
        return match.group(0)

    content = re.sub(r"(fetch\(['\"])(/[^'\"]+)(['\"])", replace_fetch, content)
    
    return content, (content != original)

def clean_existing_layout_css(content):
    """
    AGGRESSIVE CLEANUP:
    1. Removes OUR previous injections.
    2. Removes ANY OTHER <style> block that contains core layout keywords (.sidebar, .app-wrapper, etc.)
       This ensures we don't have conflicting manual definitions.
    """
    # Step A: Remove Our Own Previous Injections
    content, count_ours = OUR_PREVIOUS_INJECTION_PATTERN.subn('', content)
    if count_ours > 0:
        print(f"   🧹 REMOVED {count_ours} old self-injection(s)")

    # Step B: Remove Manual/External Style Blocks with Layout Keywords
    # We iterate through all style tags and check their content
    style_blocks = list(re.finditer(r'<style[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE))
    
    removal_indices = []
    
    for match in style_blocks:
        css_content = match.group(1)
        # Check if this style block defines critical layout elements
        # We look for specific selectors followed by opening braces
        has_sidebar_def = bool(re.search(r'\.sidebar\s*\{', css_content, re.IGNORECASE))
        has_wrapper_def = bool(re.search(r'\.app-wrapper\s*\{', css_content, re.IGNORECASE))
        has_toggle_def = bool(re.search(r'\.mobile-menu-toggle\s*\{', css_content, re.IGNORECASE))
        
        # If it defines any of these, it's considered a "Layout Core" style block and must go
        if has_sidebar_def or has_wrapper_def or has_toggle_def:
            # Record the span to remove later (reverse order to maintain indices)
            removal_indices.append((match.start(), match.end()))
            print(f"   🗑️ DETECTED MANUAL LAYOUT STYLE BLOCK TO DELETE")

    # Perform deletions in reverse order to avoid index shifting issues
    for start, end in reversed(removal_indices):
        content = content[:start] + content[end:]
        
    return content

def patch_navigation_and_css(filepath, content):
    """Replaces sidebar HTML, Cleans Old CSS, Injects New Master CSS, and Injects Loader JS."""
    parts = Path(filepath).parts
    
    # Determine Role based on directory structure
    if 'driver' in parts:
        new_sidebar_html = DRIVER_SIDEBAR_HTML
    elif 'admin' in parts:
        new_sidebar_html = ADMIN_SIDEBAR_HTML
    elif 'commuter' in parts:
        new_sidebar_html = COMMUTER_SIDEBAR_HTML
    else:
        return content, False

    # STEP 1: Clean up ALL existing layout-related CSS (Old injections + Manual styles)
    content = clean_existing_layout_css(content)

    # STEP 2: Replace Sidebar HTML Structure ALWAYS if pattern matches
    patched_content, html_count = SIDEBAR_PATTERN.subn(new_sidebar_html, content, count=1)
    
    html_changed = (html_count > 0)
    
    if not html_changed:
        # Even if no sidebar HTML was replaced, we might still need to inject CSS if the file had manual styles removed above?
        # Actually, if there's no sidebar tag, injecting CSS won't hurt but isn't strictly necessary for nav.
        # However, for consistency, let's proceed only if we actually touched the nav structure or cleaned significant CSS.
        pass 

    # STEP 3: Inject Fresh Master CSS before </head>
    # Since we deleted everything related to layout in Step 1, this is now the ONLY source of truth.
    if "</head>" in patched_content:
        patched_content = patched_content.replace("</head>", f"{MASTER_SIDEBAR_CSS}\n</head>")
    elif "<body" in patched_content:
        body_match = re.search(r'<body[^>]*>', patched_content)
        if body_match:
            insert_pos = body_match.end()
            patched_content = patched_content[:insert_pos] + "\n" + MASTER_SIDEBAR_CSS + patched_content[insert_pos:]
    else:
        patched_content += MASTER_SIDEBAR_CSS
    
    print(f"   💉 INJECTED Fresh Master CSS into {filepath}")

    # STEP 4: ALWAYS Inject Fresh JS before </body>
    # First, remove old JS injection just in case
    patched_content, js_count = BAD_INJECTION_PATTERN.subn('', patched_content)
    if js_count > 0:
         print(f"   🧹 REMOVED {js_count} old JS injection(s)")

    if "</body>" in patched_content:
        patched_content = patched_content.replace("</body>", f"{JS_INJECTION_SNIPPET}\n</body>")
    else:
        patched_content += JS_INJECTION_SNIPPET
    
    print(f"✅ NAV & CSS PATCHED (Clean Slate Applied): {filepath}")
    return patched_content, True

def process_file(filepath):
    """Processes a single file: Fixes Paths AND Patches Navigation/CSS."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        initial_content = content
        
        # Step A: Fix Paths
        content_after_paths, paths_changed = fix_paths(content)
        
        # Step B: Patch Navigation & CSS (only if it's an HTML file)
        final_content, nav_changed = content_after_paths, False
        if filepath.endswith('.html'):
            final_content, nav_changed = patch_navigation_and_css(filepath, content_after_paths)

        # Determine if ANY change happened
        was_modified = (final_content != initial_content)

        if was_modified:
            backup_path = filepath + BACKUP_SUFFIX
            if not os.path.exists(backup_path):
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    bf.write(initial_content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            status_msg = ""
            if paths_changed: status_msg += "[PATHS] "
            if nav_changed: status_msg += "[NAV+CSS] "
            print(f"💾 SAVED CHANGES ({status_msg.strip()}): {filepath}")
            return True
        else:
            return False

    except Exception as e:
        print(f"❌ ERROR processing {filepath}: {e}")
        return False

def main():
    print("🚀 Starting Master Auto-Fixer v8.2 (Delete & Replace Strategy)...")
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
