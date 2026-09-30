-- =========================================
-- Project: Pahatid System Project
-- File: database/schema_v3_unified.sql
-- Description: COMPLETE Unified Database Structure, RLS Policies, and Server-Side Logic Functions
-- Author: AI Assistant
-- Date: 2026-09-30
-- Version: 3.0.0 (Final Master Plan)
-- Target Platform: Supabase (PostgreSQL)
-- Note: This script assumes a fresh database. It handles extensions, tables, indexes, security, and logic.
-- =========================================

-- 1. ENABLE EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- Set Timezone to Philippines
SET time_zone = "+08:00";

-- --------------------------------------------------------
-- 2. TABLES DEFINITION
-- --------------------------------------------------------

-- A. PROFILES (Extends Supabase Auth Users)
-- Stores basic user info and role. Created via Trigger on signup.
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT NOT NULL,
  phone_number TEXT UNIQUE,
  role TEXT CHECK (role IN ('admin', 'dispatcher', 'driver', 'commuter')) DEFAULT 'commuter',
  avatar_url TEXT,
  status TEXT CHECK (status IN ('active', 'inactive', 'suspended', 'pending_approval')) DEFAULT 'pending_approval',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_phone ON public.profiles(phone_number);
CREATE INDEX IF NOT EXISTS idx_profiles_status ON public.profiles(status);

-- B. BRANCHES (Physical Hubs)
CREATE TABLE IF NOT EXISTS public.branches (
  branch_id SERIAL PRIMARY KEY,
  branch_code VARCHAR(20) UNIQUE NOT NULL,
  branch_name VARCHAR(100) NOT NULL,
  address TEXT NOT NULL,
  latitude DECIMAL(10, 8) NOT NULL,
  longitude DECIMAL(11, 8) NOT NULL,
  contact_number VARCHAR(20),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- C. VEHICLE_PROFILES (Standardized Specs for Calculation)
-- This table holds the "truth" for fuel efficiency, speed, and costs.
CREATE TABLE IF NOT EXISTS public.vehicle_profiles (
  profile_id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE, -- e.g., "Honda Beat", "Tricycle"
  category TEXT CHECK (category IN ('motor', 'tricycle', 'jeepney', 'car', 'van', 'custom')) DEFAULT 'motor',
  
  -- Technical Specs
  fuel_efficiency_km_per_liter DECIMAL(5, 2) NOT NULL DEFAULT 35.00,
  average_speed_kmh DECIMAL(5, 2) NOT NULL DEFAULT 30.00,
  
  -- Financial Baselines (Per Day)
  daily_rental_fee DECIMAL(10, 2) DEFAULT 0.00,
  daily_maintenance_cost DECIMAL(10, 2) DEFAULT 20.00,
  
  -- Reference Earnings (For Admin Monitoring Benchmarks)
  min_hourly_target DECIMAL(10, 2) DEFAULT 100.00,
  max_hourly_target DECIMAL(10, 2) DEFAULT 200.00,
  
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed Default Vehicles (Based on typical PH Habal-Habal stats)
INSERT INTO public.vehicle_profiles (name, category, fuel_efficiency_km_per_liter, average_speed_kmh, daily_rental_fee, daily_maintenance_cost, min_hourly_target, max_hourly_target) VALUES
('Standard Motor', 'motor', 35.00, 35.00, 0.00, 20.00, 100.00, 180.00),
('Heavy Duty Motor', 'motor', 25.00, 40.00, 0.00, 35.00, 120.00, 200.00),
('Tricycle', 'tricycle', 22.00, 25.00, 150.00, 50.00, 80.00, 150.00),
('Jeepney', 'jeepney', 8.00, 30.00, 300.00, 100.00, 150.00, 250.00),
('Private Car', 'car', 12.00, 45.00, 0.00, 50.00, 180.00, 300.00)
ON CONFLICT (name) DO NOTHING;

-- D. DRIVERS (Extended Profile)
CREATE TABLE IF NOT EXISTS public.drivers (
  driver_id SERIAL PRIMARY KEY,
  user_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
  branch_id INT REFERENCES public.branches(branch_id) ON DELETE SET NULL,
  
  -- Link to standardized vehicle specs
  preferred_vehicle_id INT REFERENCES public.vehicle_profiles(profile_id) ON DELETE SET NULL,
  
  license_number VARCHAR(50) UNIQUE NOT NULL,
  vehicle_plate_number VARCHAR(20) UNIQUE NOT NULL,
  
  current_rank TEXT CHECK (current_rank IN ('newbie', 'regular', 'senior', 'expert', 'master')) DEFAULT 'newbie',
  performance_points INT DEFAULT 0,
  average_rating DECIMAL(3, 2) DEFAULT 5.00,
  total_trips_completed INT DEFAULT 0,
  is_online BOOLEAN DEFAULT FALSE,
  
  -- Location Tracking (Decimals for JS parsing + Geography for DB queries)
  current_latitude DECIMAL(10, 8),
  current_longitude DECIMAL(11, 8),
  current_location GEOGRAPHY(Point, 4326), 
  
  last_location_update TIMESTAMP WITH TIME ZONE,
  joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spatial & Performance Indexes for Drivers
CREATE INDEX IF NOT EXISTS idx_drivers_location ON public.drivers USING GIST(current_location);
CREATE INDEX IF NOT EXISTS idx_drivers_latlng ON public.drivers(current_latitude, current_longitude);
CREATE INDEX IF NOT EXISTS idx_drivers_online ON public.drivers(is_online);

-- E. COMMUTERS (Extended Profile)
CREATE TABLE IF NOT EXISTS public.commuters (
  commuter_id SERIAL PRIMARY KEY,
  user_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
  wallet_balance DECIMAL(10, 2) DEFAULT 0.00,
  preferred_payment_method TEXT CHECK (preferred_payment_method IN ('cash', 'gcash', 'paymaya', 'wallet')) DEFAULT 'cash',
  referral_code VARCHAR(20) UNIQUE,
  referred_by_uuid UUID REFERENCES public.profiles(id) ON DELETE SET NULL
);

-- F. BOOKINGS (Core Transaction)
CREATE TABLE IF NOT EXISTS public.bookings (
  booking_id SERIAL PRIMARY KEY,
  reference_code VARCHAR(20) UNIQUE NOT NULL,
  commuter_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  driver_profile_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  
  pickup_address TEXT NOT NULL,
  pickup_lat DECIMAL(10, 8) NOT NULL,
  pickup_lng DECIMAL(11, 8) NOT NULL,
  dropoff_address TEXT NOT NULL,
  dropoff_lat DECIMAL(10, 8) NOT NULL,
  dropoff_lng DECIMAL(11, 8) NOT NULL,
  
  estimated_distance_km DECIMAL(6, 2) DEFAULT 0.00,
  actual_distance_km DECIMAL(6, 2) DEFAULT 0.00,
  
  base_fare DECIMAL(10, 2) NOT NULL,
  surge_multiplier DECIMAL(3, 2) DEFAULT 1.00,
  final_fare DECIMAL(10, 2) NOT NULL,
  
  payment_method TEXT CHECK (payment_method IN ('cash', 'wallet', 'gcash', 'paymaya')) DEFAULT 'cash',
  payment_status TEXT CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')) DEFAULT 'pending',
  trip_status TEXT CHECK (trip_status IN ('requested', 'accepted', 'arrived_pickup', 'in_progress', 'completed', 'cancelled', 'no_show')) DEFAULT 'requested',
  
  scheduled_time TIMESTAMP WITH TIME ZONE,
  started_at TIMESTAMP WITH TIME ZONE,
  ended_at TIMESTAMP WITH TIME ZONE,
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- G. TRIP_LOGS (Financial Audit Trail - The Heart of Monitoring)
-- Stores the detailed breakdown calculated by the SQL Function.
CREATE TABLE IF NOT EXISTS public.trip_logs (
  log_id BIGSERIAL PRIMARY KEY,
  driver_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  booking_id INT REFERENCES public.bookings(booking_id) ON DELETE SET NULL, 
  
  -- Route Snapshot
  pickup_lat DECIMAL(10, 8),
  pickup_lng DECIMAL(11, 8),
  dropoff_lat DECIMAL(10, 8),
  dropoff_lng DECIMAL(11, 8),
  distance_km DECIMAL(8, 2) NOT NULL,
  duration_hours DECIMAL(6, 2) NOT NULL,
  
  -- Financial Breakdown
  gross_fare DECIMAL(10, 2) NOT NULL,
  fuel_cost DECIMAL(10, 2) NOT NULL,
  rental_prorated_cost DECIMAL(10, 2) NOT NULL,
  maintenance_prorated_cost DECIMAL(10, 2) NOT NULL,
  total_expenses DECIMAL(10, 2) NOT NULL,
  net_income DECIMAL(10, 2) NOT NULL,
  
  -- Metadata
  vehicle_used_name VARCHAR(50),
  notes TEXT,
  logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Trip Logs
CREATE INDEX IF NOT EXISTS idx_trip_logs_driver_date ON public.trip_logs(driver_profile_id, logged_at DESC);
CREATE INDEX IF NOT EXISTS idx_trip_logs_booking ON public.trip_logs(booking_id);

-- H. SUPPORTING TABLES (Complaints, Reviews, Favorites, CMS)

CREATE TABLE IF NOT EXISTS public.complaints_and_warnings (
  issue_id SERIAL PRIMARY KEY,
  driver_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  reporter_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  booking_id INT REFERENCES public.bookings(booking_id) ON DELETE SET NULL,
  type TEXT CHECK (type IN ('reklamo', 'official_warning', 'commendation')) NOT NULL,
  severity_level TEXT CHECK (severity_level IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
  subject VARCHAR(150) NOT NULL,
  details TEXT NOT NULL,
  resolution_status TEXT CHECK (resolution_status IN ('open', 'investigating', 'resolved', 'dismissed')) DEFAULT 'open',
  points_adjustment INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS public.reviews_feedback (
  review_id SERIAL PRIMARY KEY,
  booking_id INT UNIQUE REFERENCES public.bookings(booking_id) ON DELETE CASCADE NOT NULL,
  commuter_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  driver_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  rating_stars SMALLINT CHECK (rating_stars >= 1 AND rating_stars <= 5),
  comment_text TEXT,
  tags JSONB DEFAULT '[]',
  is_public BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.favorite_drivers (
  commuter_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  driver_profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (commuter_profile_id, driver_profile_id)
);

-- CMS Tables
CREATE TABLE IF NOT EXISTS public.site_settings (
  setting_key VARCHAR(50) PRIMARY KEY,
  setting_value TEXT NOT NULL,
  data_type TEXT CHECK (data_type IN ('string', 'number', 'boolean', 'json')) DEFAULT 'string',
  description VARCHAR(255),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.pages_content (
  page_slug VARCHAR(50) PRIMARY KEY,
  page_title VARCHAR(100) NOT NULL,
  content_html TEXT NOT NULL,
  meta_description TEXT,
  is_published BOOLEAN DEFAULT TRUE,
  last_edited_by UUID REFERENCES public.profiles(id),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.faq_items (
  faq_id SERIAL PRIMARY KEY,
  category VARCHAR(50) DEFAULT 'General',
  question_text TEXT NOT NULL,
  answer_text TEXT NOT NULL,
  sort_order INT DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert Default CMS Data
INSERT INTO public.site_settings (setting_key, setting_value, data_type, description) VALUES
('company_name', 'Pahatid System', 'string', 'Official company name'),
('support_email', 'help@pahatidsystem.com', 'string', 'Primary support contact'),
('homepage_hero_title', 'Ride Smart, Ride Safe.', 'string', 'Main headline on landing page'),
('base_fare_php', '40.00', 'number', 'Minimum fare amount in PHP')
ON CONFLICT (setting_key) DO NOTHING;


-- --------------------------------------------------------
-- 3. ROW LEVEL SECURITY (RLS) POLICIES
-- --------------------------------------------------------

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vehicle_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.commuters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trip_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.complaints_and_warnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorite_drivers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.site_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pages_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faq_items ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist to avoid conflict during re-run
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;

-- Profiles Policies
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Admins can view all profiles" ON public.profiles FOR SELECT USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Vehicle Profiles Policies (Public Read for Drivers/Admins)
DROP POLICY IF EXISTS "Public read vehicles" ON public.vehicle_profiles;
CREATE POLICY "Public read vehicles" ON public.vehicle_profiles FOR SELECT USING (is_active = true);

-- Drivers Policies
DROP POLICY IF EXISTS "Drivers manage own record" ON public.drivers;
DROP POLICY IF EXISTS "Public can view online drivers" ON public.drivers;
CREATE POLICY "Drivers manage own record" ON public.drivers FOR ALL USING (user_profile_id = auth.uid());
CREATE POLICY "Public can view online drivers" ON public.drivers FOR SELECT USING (is_online = TRUE);

-- Commuters Policies
DROP POLICY IF EXISTS "Commuters manage own record" ON public.commuters;
CREATE POLICY "Commuters manage own record" ON public.commuters FOR ALL USING (user_profile_id = auth.uid());

-- Bookings Policies
DROP POLICY IF EXISTS "Commuters manage own bookings" ON public.bookings;
DROP POLICY IF EXISTS "Drivers manage assigned bookings" ON public.bookings;
DROP POLICY IF EXISTS "Admins manage all bookings" ON public.bookings;
CREATE POLICY "Commuters manage own bookings" ON public.bookings FOR ALL USING (commuter_profile_id = auth.uid());
CREATE POLICY "Drivers manage assigned bookings" ON public.bookings FOR ALL USING (driver_profile_id = auth.uid());
CREATE POLICY "Admins manage all bookings" ON public.bookings FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));

-- Trip Logs Policies (Critical for Security)
DROP POLICY IF EXISTS "Drivers view own logs" ON public.trip_logs;
DROP POLICY IF EXISTS "Drivers insert own logs" ON public.trip_logs;
DROP POLICY IF EXISTS "Admins view all logs" ON public.trip_logs;
CREATE POLICY "Drivers view own logs" ON public.trip_logs FOR SELECT USING (driver_profile_id = auth.uid());
CREATE POLICY "Drivers insert own logs" ON public.trip_logs FOR INSERT WITH CHECK (driver_profile_id = auth.uid());
CREATE POLICY "Admins view all logs" ON public.trip_logs FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));

-- Complaints Policies
DROP POLICY IF EXISTS "Admins view complaints" ON public.complaints_and_warnings;
DROP POLICY IF EXISTS "Reporters submit complaints" ON public.complaints_and_warnings;
CREATE POLICY "Admins view complaints" ON public.complaints_and_warnings FOR SELECT USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));
CREATE POLICY "Reporters submit complaints" ON public.complaints_and_warnings FOR INSERT WITH CHECK (reporter_profile_id = auth.uid());

-- Reviews Policies
DROP POLICY IF EXISTS "Public can view reviews" ON public.reviews_feedback;
DROP POLICY IF EXISTS "Commuters can write reviews" ON public.reviews_feedback;
CREATE POLICY "Public can view reviews" ON public.reviews_feedback FOR SELECT USING (is_public = TRUE);
CREATE POLICY "Commuters can write reviews" ON public.reviews_feedback FOR INSERT WITH CHECK (commuter_profile_id = auth.uid());

-- Favorites Policies
DROP POLICY IF EXISTS "Commuters manage favorites" ON public.favorite_drivers;
CREATE POLICY "Commuters manage favorites" ON public.favorite_drivers FOR ALL USING (commuter_profile_id = auth.uid());

-- CMS Policies
DROP POLICY IF EXISTS "Public read site settings" ON public.site_settings;
DROP POLICY IF EXISTS "Admin manage site settings" ON public.site_settings;
CREATE POLICY "Public read site settings" ON public.site_settings FOR SELECT USING (true);
CREATE POLICY "Admin manage site settings" ON public.site_settings FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));

DROP POLICY IF EXISTS "Public read published pages" ON public.pages_content;
DROP POLICY IF EXISTS "Admin manage pages" ON public.pages_content;
CREATE POLICY "Public read published pages" ON public.pages_content FOR SELECT USING (is_published = true);
CREATE POLICY "Admin manage pages" ON public.pages_content FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));

DROP POLICY IF EXISTS "Public read active FAQs" ON public.faq_items;
DROP POLICY IF EXISTS "Admin manage FAQs" ON public.faq_items;
CREATE POLICY "Public read active FAQs" ON public.faq_items FOR SELECT USING (is_active = true);
CREATE POLICY "Admin manage FAQs" ON public.faq_items FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'));


-- --------------------------------------------------------
-- 4. FUNCTIONS & TRIGGERS
-- --------------------------------------------------------

-- A. Auto-create Profile on Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, phone_number, role, status)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name', NEW.phone, 
          COALESCE(NEW.raw_user_meta_data->>'role', 'commuter'), 
          'pending_approval');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- B. Update Timestamp Helper
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE PROCEDURE public.update_updated_at_column();

-- C. CORE LOGIC: Calculate Trip Financials
-- This function performs the math server-side to prevent client manipulation.
CREATE OR REPLACE FUNCTION public.calculate_trip_financials(
    p_distance_km DECIMAL,
    p_duration_hours DECIMAL,
    p_gross_fare DECIMAL,
    p_gas_price_per_liter DECIMAL,
    p_vehicle_efficiency_km_per_liter DECIMAL,
    p_daily_rental_fee DECIMAL,
    p_daily_maintenance_cost DECIMAL,
    p_expected_work_hours DECIMAL
)
RETURNS JSONB AS $$
DECLARE
    v_liters_needed DECIMAL(10, 4);
    v_fuel_cost DECIMAL(10, 2);
    v_rental_prorated DECIMAL(10, 2);
    v_maintenance_prorated DECIMAL(10, 2);
    v_total_expenses DECIMAL(10, 2);
    v_net_income DECIMAL(10, 2);
    v_profit_margin DECIMAL(5, 2);
    v_hourly_rate DECIMAL(10, 2);
BEGIN
    -- 1. Fuel Cost
    IF p_vehicle_efficiency_km_per_liter > 0 THEN
        v_liters_needed := p_distance_km / p_vehicle_efficiency_km_per_liter;
    ELSE
        v_liters_needed := 0;
    END IF;
    v_fuel_cost := ROUND(v_liters_needed * p_gas_price_per_liter, 2);

    -- 2. Prorated Fixed Costs
    IF p_expected_work_hours > 0 THEN
        v_rental_prorated := ROUND((p_daily_rental_fee / p_expected_work_hours) * p_duration_hours, 2);
        v_maintenance_prorated := ROUND((p_daily_maintenance_cost / p_expected_work_hours) * p_duration_hours, 2);
    ELSE
        v_rental_prorated := 0;
        v_maintenance_prorated := 0;
    END IF;

    -- 3. Totals
    v_total_expenses := v_fuel_cost + v_rental_prorated + v_maintenance_prorated;
    v_net_income := p_gross_fare - v_total_expenses;

    -- 4. Metrics
    IF p_gross_fare > 0 THEN
        v_profit_margin := ROUND((v_net_income / p_gross_fare) * 100, 2);
    ELSE
        v_profit_margin := 0;
    END IF;

    IF p_duration_hours > 0 THEN
        v_hourly_rate := ROUND(v_net_income / p_duration_hours, 2);
    ELSE
        v_hourly_rate := 0;
    END IF;

    RETURN jsonb_build_object(
        'fuel_cost', v_fuel_cost,
        'rental_prorated_cost', v_rental_prorated,
        'maintenance_prorated_cost', v_maintenance_prorated,
        'total_expenses', v_total_expenses,
        'net_income', v_net_income,
        'profit_margin_percent', v_profit_margin,
        'effective_hourly_rate', v_hourly_rate
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

GRANT EXECUTE ON FUNCTION public.calculate_trip_financials TO authenticated;

COMMIT;
