#!/usr/bin/env python3
# =========================================
# Project: Pahatid System Project
# File: tools/pahatid_autofix.py
# Description: Master Auto-Fixer v8.3 (Safe Comment-Out & Inject)
# Author: Pahatid System
# Date: 2026-10-09
# Version: 8.3.0 (Comments Out Conflicting Manual CSS Instead of Deleting)
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

# Regex to FIND and REMOVE existing injected CSS blocks (Our own previous injections)
OUR_INJECTED_CSS_PATTERN = re.compile(
    r'\s*<!--\s*AUTO-INJECTED MANDATORY LAYOUT CORE BY pahatid_autofix\.py\s*-->\s*'
    r'<style>\s*'
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

# THE MANDATORY LAYOUT CORE
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

def comment_out_manual_layout_css(content):
    """
    SAFE CLEANUP:
    Finds <style> blocks that define core layout classes (.sidebar, .app-wrapper, etc.)
    and wraps their content in CSS comments /* ... */ instead of deleting them.
    This preserves the code for future reference/reverting while disabling its effect.
    """
    # Selectors that indicate a "Layout Core" style block
    layout_keywords = [
        r'\.sidebar\b',
        r'\.app-wrapper\b',
        r'\.main-content\b',
        r'\.mobile-menu-toggle\b',
        r'\.sidebar-overlay\b'
    ]

    # Find all style blocks
    style_matches = list(re.finditer(r'<style>(.*?)</style>', content, re.DOTALL | re.IGNORECASE))
    
    if not style_matches:
        return content

    new_content_parts = []
    last_end = 0

    for match in style_matches:
        start_idx = match.start()
        end_idx = match.end()
        css_body = match.group(1)
        
        # Check if this block contains our layout keywords
        has_layout_conflict = False
        for kw in layout_keywords:
            if re.search(kw, css_body, re.IGNORECASE):
                has_layout_conflict = True
                break
        
        # Add the part before this match
        new_content_parts.append(content[last_end:start_idx])
        
        if has_layout_conflict:
            print(f"    COMMENTING OUT manual layout CSS block (preserved for revert)")
            # Wrap the CSS body in comments
            commented_css = f"<style>\n/* [PAHATID_AUTO_FIX] Manual Layout Disabled to Use Master Injection */\n{css_body}\n*/\n</style>"
            new_content_parts.append(commented_css)
        else:
            # Keep as is
            new_content_parts.append(match.group(0))
            
        last_end = end_idx

    # Add remaining content after last match
    new_content_parts.append(content[last_end:])
    
    return "".join(new_content_parts)

def clean_old_injections(content):
    """Removes both old JS and Our Previous CSS injections to prepare for fresh ones."""
    content, js_count = BAD_INJECTION_PATTERN.subn('', content)
    if js_count > 0:
        print(f"   🧹 REMOVED {js_count} old JS injection(s)")
        
    content, css_count = OUR_INJECTED_CSS_PATTERN.subn('', content)
    if css_count > 0:
        print(f"   🧹 REMOVED {css_count} old CSS injection(s)")
        
    return content

def patch_navigation_and_css(filepath, content):
    """Replaces sidebar HTML, safely disables manual conflicts, injects Master CSS, and injects Loader JS."""
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

    # STEP 1: Clean up any existing OLD AUTO-INJECTIONS first
    content = clean_old_injections(content)

    # STEP 2: SAFELY COMMENT OUT MANUAL CONFLICTING CSS
    # This keeps the code but makes it inactive so our Master CSS takes over cleanly
    content = comment_out_manual_layout_css(content)

    # STEP 3: Replace Sidebar HTML Structure ALWAYS if pattern matches
    patched_content, html_count = SIDEBAR_PATTERN.subn(new_sidebar_html, content, count=1)
    
    html_changed = (html_count > 0)
    
    if not html_changed:
        return patched_content, False

    # STEP 4: INJECT MASTER CSS (Since conflicts are now commented out, this is safe)
    if "</head>" in patched_content:
        patched_content = patched_content.replace("</head>", f"{MASTER_SIDEBAR_CSS}\n</head>")
    elif "<body" in patched_content:
        body_match = re.search(r'<body[^>]*>', patched_content)
        if body_match:
            insert_pos = body_match.end()
            patched_content = patched_content[:insert_pos] + "\n" + MASTER_SIDEBAR_CSS + patched_content[insert_pos:]
    else:
        patched_content += MASTER_SIDEBAR_CSS
    
    print(f"   💉 INJECTED Fresh Master CSS")

    # STEP 5: ALWAYS Inject Fresh JS before </body>
    if "</body>" in patched_content:
        patched_content = patched_content.replace("</body>", f"{JS_INJECTION_SNIPPET}\n</body>")
    else:
        patched_content += JS_INJECTION_SNIPPET
    
    print(f"✅ NAV & CSS PATCHED (Safe Mode Applied): {filepath}")
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
    print("🚀 Starting Master Auto-Fixer v8.3 (Safe Comment-Out)...")
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
