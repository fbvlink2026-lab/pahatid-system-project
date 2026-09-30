# 🏍️ Pahatid System Project

**Version:** 3.0.0 (Final Master Plan)  
**Architecture:** Serverless Static Frontend + Supabase Backend  
**Stack:** HTML5, CSS3, Vanilla JavaScript (ES6+), Bootstrap 5, Leaflet.js, Chart.js, Quill.js  
**Database/Auth:** Supabase (PostgreSQL)  
**Hosting:** GitHub Pages  

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Setup Instructions](#setup-instructions)
   - [Step 1: Create Supabase Project](#step-1-create-supabase-project)
   - [Step 2: Configure Database Schema](#step-2-configure-database-schema)
   - [Step 3: Update Frontend Config](#step-3-update-frontend-config)
   - [Step 4: Deploy to GitHub Pages](#step-4-deploy-to-github-pages)
5. [Project Structure](#project-structure)
6. [Security Model (RLS)](#security-model-rls)
7. [Troubleshooting](#troubleshooting)
8. [License](#license)

---

## 🔭 Overview

**Pahatid System** is a comprehensive Habal-Habal transport management platform designed for the Philippines. It connects three distinct user roles through a unified, secure, and scalable serverless architecture.

Unlike traditional PHP-based systems that require expensive VPS hosting, Pahatid runs entirely on free tiers:
*   **Frontend:** Hosted statically on GitHub Pages.
*   **Backend:** Managed by Supabase (Auth, Database, Realtime, Storage).
*   **Logic:** Business rules (fare calculation, commission splits) are enforced via PostgreSQL Stored Functions, ensuring data integrity and preventing client-side manipulation.

---

## ✨ Key Features

### 👮 Admin / Dispatcher Portal
*   **Live Dispatch Map:** Real-time visualization of online drivers using Supabase Realtime subscriptions.
*   **Manual Assignment:** One-click assignment of pending bookings to nearest available drivers.
*   **Driver Management:** Approve/reject applications, adjust ranks (Newbie → Master), and suspend accounts.
*   **Financial Monitoring:** View aggregated `trip_logs` to audit driver earnings vs. expenses.
*   **Content Manager (CMS):** Edit homepage text, policies, and FAQs using a Rich Text Editor (Quill.js) without touching code.
*   **Analytics Dashboard:** KPIs for Revenue, Active Users, and Trip Completion Rates with Chart.js visualizations.

### 🏍️ Driver Portal
*   **Rate Calculator & Telemetry Hub:** 
    *   Interactive Leaflet map for route planning.
    *   Calls Supabase RPC Function `calculate_trip_financials` for precise Net Income breakdown (Fuel, Rental Proration, Maintenance).
    *   Simulated Digital Speedometer/Fuel Gauge for engagement.
*   **Task Manager:** Accept/Decline ride requests. Update trip status (Arrived, In-Progress, Completed).
*   **Profile & Rank:** View performance metrics, rating history, and rank progress.
*   **Offline Capable Logic:** Core calculations happen server-side, but UI remains responsive.

### 🚶 Commuter Portal
*   **Booking Interface:** Tap-to-select Pickup/Dropoff points on an interactive map.
*   **Real-Time Fare Estimation:** Instant cost preview based on distance and current rates.
*   **Live Order Tracking:** See driver location update in real-time without page refreshes.
*   **History & Favorites:** View past trips, receipts, and save preferred drivers.
*   **Support Tickets:** Submit complaints or inquiries linked directly to specific bookings.

---

## 🛠 Technology Stack

| Component | Technology | Purpose | Cost |
| :--- | :--- | :--- | :--- |
| **Hosting** | GitHub Pages | Static file serving (HTML/CSS/JS/Images) | Free |
| **Database** | Supabase (PostgreSQL) | Data storage, Realtime, Auth, Edge Functions | Free Tier |
| **Maps** | Leaflet.js + OpenStreetMap | GPS Tracking, Route Visualization | Free |
| **Charts** | Chart.js | Admin Analytics & Driver Reports | Free |
| **UI Framework** | Bootstrap 5 + FontAwesome | Responsive Layout & Icons | Free |
| **Rich Text** | Quill.js | CMS Content Editing | Free |

---

## 🚀 Setup Instructions

Follow these steps carefully to get your instance running.

### Step 1: Create Supabase Project
1.  Go to [supabase.com](https://supabase.com) and sign up/log in.
2.  Click **"New Project"**.
3.  Name it `Pahatid System`.
4.  Select Region: **Southeast Asia (Singapore)** recommended for PH latency.
5.  Set a strong **Database Password** and save it securely.
6.  Wait for provisioning (~2 minutes).

### Step 2: Configure Database Schema
1.  In your Supabase Dashboard, go to **SQL Editor**.
2.  Copy the contents of `database/schema_v3_unified.sql` from this repository.
3.  Paste into the SQL Editor and click **Run**.
4.  Verify success message. This creates all tables, indexes, RLS policies, and the critical `calculate_trip_financials` function.

### Step 3: Update Frontend Config
1.  Go to **Supabase Dashboard > Settings > API**.
2.  Copy your **Project URL** and **anon public** key.
3.  In this GitHub repository, open `assets/js/config.js`.
4.  Replace the placeholders:
```javascript
    const SUPABASE_URL = 'YOUR_SUPABASE_PROJECT_URL_HERE'; 
    const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_PUBLIC_KEY_HERE';
```
5.  Commit changes.

### Step 4: Deploy to GitHub Pages
1.  Go to your GitHub Repository **Settings**.
2.  Navigate to **Pages** (left sidebar).
3.  Under **Build and deployment**:
    *   Source: **Deploy from a branch**
    *   Branch: `main` / `/ (root)`
4.  Click **Save**.
5.  Wait ~1 minute. Your site will be live at:
    `https://<your-username>.github.io/<repo-name>/`

---

## 📁 Project Structure

```text
pahatid-system-project/
│
├── assets/                   # Static Resources
│   ├── css/
│   │   └── style.css         # Global Styles, Sidebar, Theme Variables
│   ├── js/
│   │   ├── config.js         # Supabase Client Init, Constants, Helpers
│   │   └── dynamic-loader.js # Fetches CMS content (Future use)
│   └── img/                  # Logos, Icons, Avatars
│
├── admin/                    # Admin Portal (Protected)
│   ├── dashboard.html        # Main Overview & Charts
│   ├── dispatch.html         # Live Map & Assignment Queue
│   ├── drivers.html          # Manage Driver Accounts & Ranks
│   ├── commuters.html        # Manage Commuter Accounts
│   ├── branches.html         # Manage Physical Hubs
│   ├── accounting.html       # Payouts & Financial Reports
│   ├── content-manager.html  # CMS Editor (Settings, Pages, FAQs)
│   └── security-keys.html    # API Key Management
│
├── driver/                   # Driver Portal (Protected)
│   ├── dashboard.html        # Home, Online Toggle, Stats
│   ├── rate-calculator.html  # THE TOOL: GPS, Math, Sync to DB
│   ├── tasks.html            # Active & Past Ride Requests
│   ├── profile.html          # Personal Info, Rank Progress
│   └── guide.html            # How-to Use Instructions
│
├── commuter/                 # Commuter Portal (Protected)
│   ├── dashboard.html        # Home, Wallet, Quick Links
│   ├── book-ride.html        # Booking Form & Map Selection
│   ├── track-order.html      # Live Tracking Interface
│   ├── history.html          # Past Trips List
│   ├── favorites.html        # Saved Drivers
│   └── support-tickets.html  # Help Center
│
├── public/                   # Public Facing Pages
│   ├── index.html            # Landing Page (SEO Optimized)
│   ├── login.html            # Unified Login/Register
│   ├── about.html            # Static About Page
│   └── contact.html          # Contact Form
│
├── database/                 # SQL Scripts
│   └── schema_v3_unified.sql # COMPLETE Database Structure + RLS + Functions
│
├── .gitignore                # Security exclusions
├── .env.example              # Template for local dev keys
├── README.md                 # This documentation
└── LICENSE                   # MIT License
```

---

## 🔒 Security Model (RLS)

We utilize **Row Level Security (RLS)** in PostgreSQL to ensure data isolation. Even if a hacker inspects the network traffic or obtains the `anon public` key, they cannot access unauthorized data.

*   **Drivers:** Can only `SELECT`, `INSERT`, `UPDATE` their own records in `drivers`, `trip_logs`, and assigned `bookings`.
*   **Commuters:** Can only manage their own `commuters` profile, `bookings`, and `reviews`.
*   **Admins:** Have full CRUD access to all tables.
*   **Public/Guests:** Can only read `site_settings`, `pages_content`, `faq_items`, and `vehicle_profiles`. Cannot see user data.

The core financial logic resides in the SQL function `calculate_trip_financials`. The frontend sends raw inputs (distance, time, fare) to this function, and the database returns the calculated breakdown. This prevents clients from manipulating expense figures.

---

## ❓ Troubleshooting

**Issue:** Site loads but shows "Supabase Credentials not set!" warning.  
**Fix:** Ensure you replaced the placeholders in `assets/js/config.js` with actual URLs/Keys from Supabase Settings > API.

**Issue:** Login fails immediately after registration.  
**Fix:** Check Supabase Authentication settings. By default, email confirmation might be enabled. For development, disable "Confirm email" in Supabase Auth > Providers > Email.

**Issue:** Maps do not load.  
**Fix:** Ensure you have internet connection. Leaflet tiles are loaded from OpenStreetMap CDN. Also, check browser console for CORS errors (rare with OSM, but possible if blocked by extensions).

**Issue:** SQL Script fails to run.  
**Fix:** Ensure you are running it in the **SQL Editor**, not the Table Editor. Make sure no previous partial scripts exist that conflict with `DROP TABLE` commands.

---

## 📄 License

MIT License

Copyright (c) 2026 Pahatid Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
