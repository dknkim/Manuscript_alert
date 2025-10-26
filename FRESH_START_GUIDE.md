# Fresh Start: Username-First Authentication

> **Quick Setup Guide for Manuscript Alert System**
> Setting up your own instance with Supabase backend

## What You're Building

A manuscript alert system with:
- **Username + password** login (email is optional)
- **Role-based access** (admin/user/guest)
- **Cloud database** with Supabase
- **Secure** with Row Level Security

---

## What You'll Need

- A Supabase account (free tier works fine)
- Python 3.8+ installed
- 15 minutes

---

## Step 1: Create Your Supabase Project

1. **Sign up at** [supabase.com](https://supabase.com) (if you haven't already)
2. **Click "New Project"**
3. **Choose a project name** and set a database password
4. **Wait for setup to complete** (~2 minutes)
5. **Save your project URL** - you'll need it later

---

## Step 2: Create Database Schema

1. **Go to SQL Editor** in your Supabase dashboard
   - Navigate to: SQL Editor (left sidebar)
   - Click "New Query"

2. **Copy ALL contents from** `DROP_AND_RECREATE.sql`

3. **Paste and click "Run"**

This will:
- ✅ Create all database tables
- ✅ Set up username-first authentication
- ✅ Configure Row Level Security (RLS) policies
- ✅ Insert default system settings

**Note:** If you have existing tables, this will drop them! Only use for fresh setup.

---

## Step 3: Create Your First Admin User

### Method 1: Using Supabase Dashboard (Easiest)

1. **Go to Authentication → Users** in your Supabase dashboard

2. **Click "Add user"**

3. **Fill in:**
   ```
   Email: admin@localhost  (or any email - it's optional anyway)
   Password: [your secure password]

   ☑ Auto Confirm User (IMPORTANT: Check this box!)
   ```

4. **Click "Create user"** and **copy the UUID** shown

5. **Go back to SQL Editor** and run this (replace UUID):

```sql
-- Create admin profile (replace UUID and details)
INSERT INTO user_profiles (
  id,
  username,
  email,
  full_name,
  role,
  is_active
)
VALUES (
  'PASTE_USER_UUID_HERE',    -- UUID from step 4
  'admin',                    -- Your username for login
  'admin@yourdomain.com',     -- Optional, can be NULL
  'System Administrator',     -- Display name
  'admin',                    -- Role
  TRUE                        -- Active status
);
```

### Method 2: Using Python Script (Alternative)

If you prefer automation, use `check_and_fix_admin.py`:

```bash
# First, set up your .env file (see Step 4)
python check_and_fix_admin.py
```

This will find any orphaned auth users and create profiles for them.

---

## Step 5: Get Your API Keys

1. **Go to Project Settings → API** in Supabase dashboard

2. **Copy these values:**
   - `Project URL`
   - `anon public` key
   - `service_role` key (keep this SECRET!)

3. **Create `.env` file** in your project root:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

**IMPORTANT:** Never commit `.env` to git! It's already in `.gitignore`.

---

## Step 6: Install Python Dependencies

```bash
pip install supabase python-dotenv
```

---

## Step 7: Test Your Setup

```bash
python test_supabase_connection.py
```

You should see:
```
✅ Connection to Supabase: SUCCESS
✅ Database access successful
✅ User profiles found: 1 user(s)
✅ Admin user configured correctly!
✅ System settings: 4 settings loaded
```

**If you see errors:**
- Check your `.env` file has correct keys
- Verify admin user was created in Step 3
- Run `python check_and_fix_admin.py` to fix orphaned users

---

## 🎉 You're Done!

Your Manuscript Alert System is now set up with:
- ✅ Cloud database on Supabase
- ✅ Username-based authentication
- ✅ Admin user created
- ✅ Row Level Security enabled
- ✅ Ready for development

**Next Steps:**
- Start building your Streamlit UI
- Implement login/logout functionality
- Migrate your paper data to Supabase

---

## Understanding the Authentication Model

### Creating Users

**OLD WAY:**
```python
# Had to create with email
supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "password123"
})
```

**NEW WAY:**
```python
# Create auth user with any email (or fake one)
response = supabase.auth.sign_up({
    "email": "user@temp.com",  # Can be temporary/fake
    "password": "password123"
})

# Then create profile with REAL username
supabase.table('user_profiles').insert({
    "id": response.user.id,
    "username": "john_doe",      # REQUIRED - this is login ID
    "email": "real@email.com",   # OPTIONAL - for notifications
    "full_name": "John Doe",
    "role": "user"
}).execute()
```

### Login Flow

**Users login with USERNAME:**
```python
# Find user by username first
profile = supabase.table('user_profiles')\
                 .select('id, email')\
                 .eq('username', username)\
                 .single()\
                 .execute()

# Then authenticate with their email/password
supabase.auth.sign_in_with_password({
    "email": profile.data['email'],  # Get email from profile
    "password": password
})
```

---

## Authentication Model Summary

```
┌─────────────────────────────────────────┐
│         USER WANTS TO LOGIN             │
└────────────────┬────────────────────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Enter USERNAME│  ← Primary identifier
         │ Enter PASSWORD│
         └───────┬───────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ Lookup username in         │
    │ user_profiles table        │
    └────────┬───────────────────┘
             │
             ▼
   ┌─────────────────────────┐
   │ Get email from profile  │
   │ (internal use only)     │
   └──────────┬──────────────┘
              │
              ▼
   ┌──────────────────────────┐
   │ Authenticate with        │
   │ Supabase Auth using      │
   │ email + password         │
   └──────────┬───────────────┘
              │
              ▼
         ┌─────────┐
         │ SUCCESS │
         └─────────┘
```

**Email is optional and only used for:**
- Password reset emails
- Notification emails
- Account recovery

**Username is:**
- Required
- Unique
- Primary login identifier
- What users remember and use
