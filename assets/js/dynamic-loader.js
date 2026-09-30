// =========================================
// Project: Pahatid System Project
// File: assets/js/dynamic-loader.js
// Description: Fetches dynamic content from Supabase CMS tables and injects into DOM
// Author: Pahatid System
// Date: 2026-09-30
// Version: 3.0.0 (Final Master Plan)
// Usage: Import this module in any HTML page that needs dynamic content.
//        Add data-cms-key="..." attributes to HTML elements you want to populate.
// =========================================

import { supabase } from './config.js';

/**
 * Initializes the Dynamic Content Loader.
 * Scans the DOM for elements with [data-cms-key] and populates them.
 */
export async function initDynamicContent() {
    if (!supabase) {
        console.warn("⚠️ Supabase client not initialized. Skipping dynamic load.");
        return;
    }

    // 1. Identify all elements needing dynamic data
    const cmsElements = document.querySelectorAll('[data-cms-key]');
    
    if (cmsElements.length === 0) {
        return; // Nothing to do
    }

    // Group keys by table/source to minimize network requests
    // Sources: 'site_settings' (simple key-value) and 'pages_content' (rich text/html)
    const settingsKeys = [];
    const pageSlugs = [];

    cmsElements.forEach(el => {
        const key = el.getAttribute('data-cms-key');
        const type = el.getAttribute('data-cms-type') || 'setting'; // Default to setting
        
        if (type === 'page') {
            pageSlugs.push(key);
        } else {
            settingsKeys.push(key);
        }
    });

    try {
        // 2. Fetch Site Settings (Batch Request)
        if (settingsKeys.length > 0) {
            const uniqueSettings = [...new Set(settingsKeys)];
            
            const { data: settingsData, error: settingsErr } = await supabase
                .from('site_settings')
                .select('*')
                .in('setting_key', uniqueSettings);

            if (settingsErr) throw settingsErr;

            // Map results back to DOM
            const settingsMap = {};
            settingsData.forEach(item => {
                settingsMap[item.setting_key] = item.setting_value;
            });

            applySettingsToDOM(cmsElements, settingsMap);
        }

        // 3. Fetch Page Content (Individual Requests for simplicity, or batch if optimized later)
        if (pageSlugs.length > 0) {
            const uniqueSlugs = [...new Set(pageSlugs)];
            
            for (const slug of uniqueSlugs) {
                const { data: pageData, error: pageErr } = await supabase
                    .from('pages_content')
                    .select('*')
                    .eq('page_slug', slug)
                    .single();

                if (pageErr) {
                    console.error(`Failed to load page: ${slug}`, pageErr);
                    continue;
                }

                applyPageToDOM(cmsElements, slug, pageData);
            }
        }

    } catch (error) {
        console.error("Critical Error in Dynamic Loader:", error);
        // Optional: Show a fallback message or hide loading spinners
    }
}

/**
 * Applies fetched settings values to matching DOM elements
 */
function applySettingsToDOM(elements, settingsMap) {
    elements.forEach(el => {
        const key = el.getAttribute('data-cms-key');
        const type = el.getAttribute('data-cms-type') || 'setting';
        
        if (type !== 'page' && settingsMap[key] !== undefined) {
            const value = settingsMap[key];
            
            // Determine how to inject based on element type or attribute
            const targetAttr = el.getAttribute('data-cms-target'); // e.g., 'href', 'src', 'innerText'
            
            if (targetAttr) {
                el.setAttribute(targetAttr, value);
            } else if (el.tagName === 'IMG') {
                el.src = value;
            } else if (el.tagName === 'A') {
                el.href = value;
            } else {
                // Default: Inject as HTML (allows bold/tags if stored in DB)
                // Use innerText for security if content is plain text only
                el.innerHTML = value; 
            }
            
            // Remove placeholder styling/loading state
            el.classList.remove('cms-loading');
        }
    });
}

/**
 * Applies fetched page content to matching DOM elements
 */
function applyPageToDOM(elements, slug, pageData) {
    elements.forEach(el => {
        if (el.getAttribute('data-cms-key') === slug && el.getAttribute('data-cms-type') === 'page') {
            // Usually, page content replaces the entire innerHTML of a container div
            el.innerHTML = pageData.content_html;
            el.classList.remove('cms-loading');
        }
    });
}

// Auto-initialize when DOM is ready if imported directly
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDynamicContent);
} else {
    initDynamicContent();
}
