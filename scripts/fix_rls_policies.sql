-- ============================================================
-- Kyro — RLS Policy Patch (run AFTER the main schema)
-- Fixes infinite recursion by using auth.jwt() instead of
-- subquerying the profiles table from its own policy.
-- ============================================================

-- Drop and recreate profiles policies
DROP POLICY IF EXISTS "Profiles are viewable by same hospital members" ON profiles;
CREATE POLICY "Profiles are viewable by same hospital members" 
ON profiles FOR SELECT 
USING (hospital_id = (auth.jwt() -> 'user_metadata' ->> 'hospital_id')::uuid);

DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile"
ON profiles FOR INSERT
WITH CHECK (id = auth.uid());

DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile" 
ON profiles FOR UPDATE 
USING (id = auth.uid());

-- Drop and recreate clinical data policies
DROP POLICY IF EXISTS "Scoped hospital access: patients" ON patients;
CREATE POLICY "Scoped hospital access: patients" 
ON patients FOR ALL 
USING (hospital_id = (auth.jwt() -> 'user_metadata' ->> 'hospital_id')::uuid);

DROP POLICY IF EXISTS "Scoped hospital access: doctors" ON doctors;
CREATE POLICY "Scoped hospital access: doctors" 
ON doctors FOR ALL 
USING (hospital_id = (auth.jwt() -> 'user_metadata' ->> 'hospital_id')::uuid);

DROP POLICY IF EXISTS "Scoped hospital access: triage_logs" ON triage_logs;
CREATE POLICY "Scoped hospital access: triage_logs" 
ON triage_logs FOR ALL 
USING (hospital_id = (auth.jwt() -> 'user_metadata' ->> 'hospital_id')::uuid);

-- Done  
SELECT 'RLS policies patched successfully' AS status;
