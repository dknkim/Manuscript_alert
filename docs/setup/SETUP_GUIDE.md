# Manuscript Alert System - Setup Guide

## Quick Setup (Email-Based Authentication)

### Prerequisites
- Supabase account (free tier)
- Python 3.8+
- 15 minutes

---

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Save your project URL and database password

---

## Step 2: Deploy Database Schema

1. Go to **SQL Editor** in Supabase dashboard
2. Copy contents from `DROP_AND_RECREATE_EMAIL_AUTH.sql`
3. Paste and click **"Run"**

This creates all tables with email-based authentication.

---

## Step 3: Get API Keys

**Settings → API** in Supabase:
- Copy `Project URL`
- Copy `anon public` key  
- Copy `service_role` key (keep secret!)

Create `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

## Step 4: Install Dependencies

```bash
pip install supabase python-dotenv
```

---

## Step 5: Create Admin User

```bash
python utils/admin_tools/create_admin_email.py
```

Enter your email and password.

---

## Step 6: Test & Run

```bash
# Test connection
python test_supabase_connection.py

# Start app
streamlit run app.py
```

---

## Adding More Users

**Method 1: Self-Registration**
- Users visit app and click "Sign Up Instead"

**Method 2: Admin Creates Them**
```bash
python utils/admin_tools/create_admin_email.py
```

**Promote to Admin:**
```bash
python utils/admin_tools/promote_to_admin.py
```

---

See [USER_GUIDE.md](../USER_GUIDE.md) for complete documentation.
