// =========================================
// Project: Pahatid System Project
// File: assets/js/config.js
// Description: Global Configuration, Supabase Client Initialization, and Utility Helpers
// Author: AI Assistant
// Date: 2026-09-30
// Version: 3.0.0 (Final Master Plan)
// Note: This file uses ES Modules. Ensure your HTML scripts use type="module".
// =========================================

import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

// --- CONFIGURATION PLACEHOLDERS ---
// IMPORTANT: Replace these values with your actual credentials from Supabase Dashboard > Settings > API
const SUPABASE_URL = 'https://tbmbidkujqwoexwkmovv.supabase.co'; 
const SUPABASE_ANON_KEY = 'sb_publishable_pt5Gq6JdzWrxnV0J0MyaJQ_dAX4Qk25';

// --- GLOBAL CONSTANTS ---
export const APP_CONFIG = {
    appName: 'Pahatid System',
    currencySymbol: '₱',
    locale: 'en-PH',
    defaultLanguage: 'en',
    
    // Fare Calculation Defaults (Fallbacks if DB fails or for simple estimates)
    fares: {
        baseFare: 40.00,
        ratePerKm: 15.00,
        minimumFare: 50.00,
        surgeMaxMultiplier: 2.50
    },

    // Roles
    roles: {
        ADMIN: 'admin',
        DISPATCHER: 'dispatcher',
        DRIVER: 'driver',
        COMMUTER: 'commuter'
    },

    // Trip Statuses
    statuses: {
        REQUESTED: 'requested',
        ACCEPTED: 'accepted',
        ARRIVED_PICKUP: 'arrived_pickup',
        IN_PROGRESS: 'in_progress',
        COMPLETED: 'completed',
        CANCELLED: 'cancelled',
        NO_SHOW: 'no_show'
    },

    // Driver Ranks
    ranks: ['newbie', 'regular', 'senior', 'expert', 'master'],

    // Expense Categories
    expenseCategories: [
        { value: 'fuel_gasoline', label: 'Fuel / Gasoline' },
        { value: 'oil_change', label: 'Oil Change' },
        { value: 'tire_replacement', label: 'Tire Replacement' },
        { value: 'parts_maintenance', label: 'Parts & Maintenance' },
        { value: 'daily_rental_fee', label: 'Daily Rental Fee' },
        { value: 'food_meals', label: 'Food / Meals' },
        { value: 'parking_toll', label: 'Parking / Toll' },
        { value: 'other', label: 'Other' }
    ]
};

// --- INITIALIZE SUPABASE CLIENT ---
let supabase;

if (SUPABASE_URL.includes('YOUR_SUPABASE')) {
    console.warn("⚠️ WARNING: Supabase Credentials not set! Please update 'assets/js/config.js' with your actual Project URL and Anon Key.");
    // Create a dummy client to prevent immediate crash during dev setup, but it won't work for real requests
    try {
        supabase = createClient('https://dummy.supabase.co', 'dummy-key');
    } catch (e) {
        console.error("Failed to initialize even dummy Supabase client.", e);
    }
} else {
    try {
        supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    } catch (error) {
        console.error("Failed to initialize Supabase:", error);
    }
}

// Export the client instance for use in other modules
export { supabase };

// --- HELPER FUNCTIONS ---

/**
 * Formats a number as Philippine Peso currency
 * @param {number} amount 
 * @returns {string} Formatted string e.g., ₱1,234.56
 */
export function formatCurrency(amount) {
    return new Intl.NumberFormat(APP_CONFIG.locale, {
        style: 'currency',
        currency: 'PHP',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Generates a unique Reference Code for bookings
 * Format: PH-YYYYMMDD-XXXXXX
 * @returns {string}
 */
export function generateRefCode() {
    const datePart = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const randomPart = Math.random().toString(36).substring(2, 8).toUpperCase();
    return `PH-${datePart}-${randomPart}`;
}

/**
 * Calculates estimated fare based on distance
 * Logic: Base Fare + (Distance * Rate Per Km)
 * Applies Minimum Fare constraint
 * @param {number} distanceKm 
 * @returns {number} Estimated Fare
 */
export function calculateEstimatedFare(distanceKm) {
    let fare = APP_CONFIG.fares.baseFare + (distanceKm * APP_CONFIG.fares.ratePerKm);
    
    if (fare < APP_CONFIG.fares.minimumFare) {
        fare = APP_CONFIG.fares.minimumFare;
    }

    return parseFloat(fare.toFixed(2));
}

/**
 * Checks if user is logged in and returns their profile data
 * @returns {Promise<Object|null>} Profile object or null
 */
export async function getAuthUser() {
    if (!supabase) return null;
    
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error || !session) return null;

    // Fetch additional profile data from our custom table
    const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', session.user.id)
        .single();

    if (profileError) {
        console.error("Profile fetch error:", profileError);
        return null;
    }

    return { ...session.user, ...profile };
}

/**
 * Redirects user if not authenticated or wrong role
 * Call this at the top of protected pages (Admin/Driver/Commuter dashboards)
 * @param {Array<string>} allowedRoles List of roles permitted to access the page
 */
export async function requireAuth(allowedRoles = []) {
    const user = await getAuthUser();
    
    if (!user) {
        window.location.href = '/login.html';
        return false;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
        alert(`Access Denied. You need ${allowedRoles.join(' or ')} privileges.`);
        window.location.href = '/index.html'; // Or appropriate redirect
        return false;
    }

    return true;
}
