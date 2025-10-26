-- Create first admin user
-- This assumes you've already created an auth.users entry via Supabase dashboard
-- Replace the UUID with your actual auth user UUID

-- Step 1: First create the auth user in Supabase Dashboard:
-- Go to: Authentication → Users → Add user
-- Email: admin@localhost (or any email)
-- Password: [your secure password]
-- Auto Confirm User: ✓

-- Step 2: Copy the UUID from that user

-- Step 3: Run this SQL with your UUID:
INSERT INTO user_profiles (
  id,
  username,
  email,
  full_name,
  role,
  is_active
)
VALUES (
  'PASTE_YOUR_AUTH_USER_UUID_HERE',  -- Get from auth.users
  'admin',                             -- Your login username
  'admin@localhost',                   -- Optional email
  'System Administrator',              -- Display name
  'admin',                            -- Role
  TRUE                                -- Active
);

-- Verify it worked:
SELECT username, email, role, is_active FROM user_profiles;
