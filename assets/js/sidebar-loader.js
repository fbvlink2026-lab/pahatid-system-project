// assets/js/sidebar-loader.js
import { supabase } from './config.js';

/**
 * Loads the sidebar dynamically based on User Role
 * @param {string} containerId - The ID of the <ul> element in HTML
 * @param {string} userRole - 'admin', 'driver', or 'commuter'
 */
export async function loadDynamicSidebar(containerId, userRole) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
        // 1. Fetch ONLY active menus for THIS specific role
        // This query ensures a driver NEVER sees admin links
        const { data, error } = await supabase
            .from('navigation_menu')
            .select('*')
            .eq('role_access', userRole) // STRICT FILTER BY ROLE
            .eq('is_active', true)
            .order('sort_order', { ascending: true });

        if (error) throw error;

        if (!data || data.length === 0) {
            container.innerHTML = '<li class="text-muted p-3">No navigation available.</li>';
            return;
        }

        // 2. GROUP BY SECTION HEADER for clean UI
        const grouped = {};
        data.forEach(item => {
            const section = item.section_header || 'Menu';
            if (!grouped[section]) grouped[section] = [];
            grouped[section].push(item);
        });

        // 3. RENDER HTML
        let htmlContent = '';
        
        Object.keys(grouped).forEach(sectionName => {
            // Add Section Header Label (e.g., "Finance", "Account")
            htmlContent += `<li class="nav-item mt-3 mb-1 px-3 small text-uppercase text-secondary fw-bold">${sectionName}</li>`;

            grouped[sectionName].forEach(item => {
                const isLogout = item.label.toLowerCase().includes('logout');
                
                // Determine CSS Classes
                const linkClass = isLogout 
                    ? 'nav-link text-danger py-2 px-3 rounded hover-bg-dark mt-2' 
                    : 'nav-link text-light py-2 px-3 rounded hover-bg-dark';
                
                const idAttr = isLogout ? 'id="dynamicLogoutBtn"' : '';
                
                // Highlight Active Page (Simple check using current URL filename)
                const currentPageFile = window.location.pathname.split('/').pop();
                const targetPageFile = item.url.split('/').pop();
                const isActive = currentPageFile === targetPageFile;
                const activeClass = isActive ? 'bg-primary text-white shadow-sm' : '';

                htmlContent += `
                    <li class="nav-item mb-1">
                        <a href="${item.url}" class="${linkClass} ${activeClass}" ${idAttr}>
                            <i class="${item.icon_class} me-2"></i> ${item.label}
                        </a>
                    </li>
                `;
            });
        });

        container.innerHTML = htmlContent;

        // 4. ATTACH LOGOUT EVENT LISTENER
        const logoutBtn = document.getElementById('dynamicLogoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                if(confirm("Are you sure you want to logout?")) {
                    await supabase.auth.signOut();
                    window.location.href = '/pahatid-system-project/login.html';
                }
            });
        }

    } catch (err) {
        console.error("Failed to load sidebar:", err);
        container.innerHTML = '<li class="text-danger p-3"><i class="fas fa-exclamation-triangle me-2"></i>Error loading navigation.</li>';
    }
}
