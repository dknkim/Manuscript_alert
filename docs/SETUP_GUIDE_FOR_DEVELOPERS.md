# Manuscript Alert System - Developer Setup Guide

## For New Team Members (First-Time Supabase Users)

This guide will walk you through setting up the Manuscript Alert System with Supabase integration on your local machine.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Supabase Setup (Step-by-Step)](#supabase-setup-step-by-step)
4. [Local Environment Setup](#local-environment-setup)
5. [Connecting to Existing Database](#connecting-to-existing-database)
6. [Testing Your Setup](#testing-your-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.9+** installed
- **Git** installed
- **Code editor** (VS Code, PyCharm, etc.)
- **Terminal/Command Line** access
- **Internet connection** (for Supabase access)

---

## Understanding the Architecture

### What is Supabase?

Supabase is a cloud database service (like Firebase, but uses PostgreSQL). Think of it as:

- **Remote Database**: Stores user accounts, preferences, and paper data
- **Authentication Service**: Handles login/signup
- **Real-time Sync**: Changes sync across devices automatically

### How Our System Works

```
Your Computer                          Project Owner's Supabase
┌─────────────┐                       ┌──────────────────┐
│             │                       │                  │
│ Streamlit   │ ←─ API Calls ────────→│  PostgreSQL DB   │
│ Web App     │   (Python Client)     │  (Deployment)    │
│             │                       │                  │
│             │                       │  - Users         │
│             │                       │  - Preferences   │
│             │                       │  - Papers        │
└─────────────┘                       └──────────────────┘
        ↑                                       ↑
        │                                       │
    You (Team Member)                 Project Owner's Account
                                      (Project Owner)
```

**Important**:
- **ONE Supabase project** created by your project owner (deployment server)
- **Multiple developers** connect to the SAME project using shared credentials
- **Project owner** (project owner) creates the Supabase account and project
- **You (team member)** receive credentials from project owner to connect

---

## Supabase Setup (Step-by-Step)

### Two Paths Based on Your Role

---

## PATH A: For Project Owner (Creating the Supabase Project)

**👤 You are: The team member who will host the deployment server**

### Step 1: Create Supabase Account

1. **Go to**: https://supabase.com
2. **Click**: "Start your project"
3. **Sign up** with:
   - GitHub (recommended - easier for team collab)
   - OR Email/password

4. **Verify** your email if required

### Step 2: Create New Project

1. **Click**: "New Project"
2. **Fill in details**:
   - **Name**: `Manuscript Alert Production` (or similar)
   - **Database Password**: Create a STRONG password (save it!)
   - **Region**: Choose closest to your location (e.g., `us-west-1`)
   - **Pricing Plan**: Select **Free** (sufficient for development)

3. **Click**: "Create new project"
4. **Wait**: ~2 minutes for project to provision

### Step 3: Get Your API Keys

1. **Go to**: Project Settings → API
   - URL: `https://supabase.com/dashboard/project/[your-project-id]/settings/api`

2. **Copy these values**:
   ```
   Project URL: https://[your-project-id].supabase.co
   anon public key: eyJhbGci... (long string)
   service_role key: eyJhbGci... (different long string)
   ```

3. **Save them securely** (you'll share these with your team)

### Step 4: Set Up Database Schema

You need to run the migration scripts to create tables:

```bash
# On your machine, after cloning the repo:
cd Manuscript_alert

# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref [your-project-id]

# Push migrations to create all tables
supabase db push
```

**Alternative (if CLI doesn't work):**
1. Go to SQL Editor: `https://supabase.com/dashboard/project/[your-project-id]/sql`
2. Run each migration file manually from `supabase/migrations/`:
   - `20251027000000_email_based_auth.sql` (run this first)
   - `20251027000001_user_preferences_table.sql` (run this second)

### Step 5: Create First Admin User

```bash
# Create your admin account
python -m utils.admin_tools.create_admin_email

# Enter your details:
# Email: your.email@gmail.com
# Full Name: Your Name
# Role: admin
# Password: (create a strong password)
```

### Step 6: Share Credentials with Team

**⚠️ IMPORTANT: Share these via SECURE channel (Signal, 1Password, etc.)**

Send your team members:
```
SUPABASE_URL=https://[your-project-id].supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]
```

**Also share** (via SQL Editor or admin tool):
- Create user accounts for each team member
- Share their login credentials

### Step 7: Verify Setup

1. **Test connection**:
```bash
python -c "from services.supabase_client import get_supabase_client; print('✅ Connected!' if get_supabase_client() else '❌ Failed')"
```

2. **Start app**:
```bash
streamlit run app.py
```

3. **Login** with your admin account
4. **Verify**: Can you see Settings → My Profile?

---

## PATH B: For Team Members (Connecting to Existing Project)

**👤 You are: A team member connecting to the deployment server**

### Step 1: Get Credentials from Project Owner

**Ask your project owner (project owner) for:**

1. **Supabase Project Credentials**:
   ```
   SUPABASE_URL=https://[project-id].supabase.co
   SUPABASE_ANON_KEY=eyJhbGci... (long string)
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (different long string)
   ```

2. **Your User Account**:
   ```
   Email: your.email@gmail.com
   Password: (temporary password)
   ```

**⚠️ Important**: Request these via SECURE channel (Signal, ProtonMail, etc.)

### Step 2: You DON'T Need To

❌ Create a Supabase account
❌ Create a new project
❌ Run database migrations
❌ Set up tables or schemas

✅ You ONLY need the credentials above!

### Step 3: Continue to "Local Environment Setup" below

---

## Which Path Are You?

**Project Owner** (creates Supabase account):
- ✅ Follow PATH A above
- ✅ Share credentials with team
- ✅ You control the deployment server

**Team Member** (connects to existing):
- ✅ Follow PATH B above
- ✅ Get credentials from project owner
- ✅ You connect to their server

---

## Local Environment Setup

### Step 1: Clone the Repository

```bash
# Navigate to where you want the project
cd ~/code  # or your preferred directory

# Clone the repository
git clone <repository-url>

# Enter the project directory
cd Manuscript_alert
```

### Step 2: Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Create Your `.env` File

The `.env` file stores your Supabase credentials **locally** and is **NOT tracked by git** (for security).

```bash
# Copy the example file
cp .env.example .env

# Open .env in your editor
# Example using nano:
nano .env

# Or using VS Code:
code .env
```

### Step 4: Configure Your `.env` File

Replace the placeholder values with credentials from your team lead:

```bash
# .env file contents

# Supabase Configuration
# Get these from your project owner (project owner)

SUPABASE_URL=https://lrlefufmpvxhfumbtuwc.supabase.co
SUPABASE_ANON_KEY=<paste_anon_key_here>
SUPABASE_SERVICE_ROLE_KEY=<paste_service_role_key_here>
```

**Where to get these values:**

1. **Ask your team lead for these 3 values**
2. **DO NOT** commit `.env` to git (it's in `.gitignore`)
3. **DO NOT** share these keys publicly (Slack messages, etc.)

**Example of what real keys look like** (not actual keys):
```bash
SUPABASE_URL=https://lrlefufmpvxhfumbtuwc.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSI...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIi...
```

### Step 5: Verify Your Setup

Test that everything is connected:

```bash
# Test Supabase connection
python -c "from services.supabase_client import get_supabase_client; print('✅ Connection successful!' if get_supabase_client() else '❌ Connection failed')"
```

**Expected output:**
```
✅ Connection successful!
```

---

## Connecting to Existing Database

### Understanding Shared Database

**Key concept**: Everyone on the team connects to the **SAME** Supabase database.

```
Shared Supabase Database
┌────────────────────────────┐
│                            │
│  Users Table:              │
│  - Project owner (admin)   │
│  - Team member 1 (admin)   │
│  - Team member 2 (user)    │
│                            │
│  Papers Table:             │
│  - Shared papers           │
│  - Everyone sees same data │
│                            │
└────────────────────────────┘
         ↑           ↑
         │           │
  Project Owner   Team Member
```

### Creating Your User Account

**Option 1: Team Lead Creates It (Recommended)**

Ask your team lead to run:
```bash
python -m utils.admin_tools.create_admin_email
```

They'll enter:
- Your email: `your.email@gmail.com`
- Your name: `Your Name`
- Your role: `user` or `admin`
- Password: (they'll share with you securely)

**Option 2: Self-Registration (If Enabled)**

1. Run the app: `streamlit run app.py`
2. Click "Sign Up Instead"
3. Fill in your details
4. Wait for admin to promote you (if you need admin access)

---

## Testing Your Setup

### Test 1: Start the Application

```bash
# Make sure you're in the project directory
cd Manuscript_alert

# Start Streamlit
streamlit run app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

### Test 2: Login

1. **Open browser**: Go to http://localhost:8501
2. **You should see**: "🔐 Login to Manuscript Alert System"
3. **Enter credentials**: Email + password from team lead
4. **Expected result**: Welcome screen with your name in top-right

### Test 3: Verify Database Access

After logging in:

1. **Go to Settings tab** → "My Profile"
2. **Check**: Can you see your profile data?
3. **Try changing**: Your full name and save
4. **Verify**: Does it persist after page refresh?

### Test 4: Check Shared Data

1. **Go to Papers tab**
2. **Enter keywords**: (any research terms)
3. **Click "Refresh Data"**
4. **Expected**: Papers should load from API

**Note**: If your team lead has already saved papers, you should see them too!

---

## What You Need to Share with Team Members

### For MCP (Model Context Protocol) Login

If you're using Supabase MCP (advanced feature), you need:

1. **Supabase Project URL**: `https://lrlefufmpvxhfumbtuwc.supabase.co`
2. **Supabase Anon Key**: (the public key from `.env`)
3. **Your user account credentials**: Email + password

**MCP Setup** (if you're using Claude Desktop or similar):

```json
// Add to your MCP config file
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--supabase-url", "https://lrlefufmpvxhfumbtuwc.supabase.co",
        "--supabase-key", "<your-anon-key-here>"
      ]
    }
  }
}
```

### What's in `.env.example` (For Reference Only)

The `.env.example` file is a **template** that shows what your `.env` should look like:

```bash
# .env.example (checked into git - safe to share)
SUPABASE_URL=https://lrlefufmpvxhfumbtuwc.supabase.co
SUPABASE_ANON_KEY=your_anon_public_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_secret_key_here
```

**Important:**
- ✅ `.env.example` is in git (shows structure only)
- ❌ `.env` is NOT in git (contains real secrets)
- ⚠️ Never commit `.env` to version control

---

## Troubleshooting

### Problem 1: "Connection failed" Error

**Error message:**
```
❌ Connection failed
```

**Possible causes:**
1. Wrong credentials in `.env`
2. `.env` file not in project root
3. Supabase project is down

**Solution:**
```bash
# Check if .env exists
ls -la .env

# Verify .env has correct values (no quotes needed)
cat .env

# Test connection with verbose output
python -c "
from services.supabase_client import get_supabase_client
import os
print('URL:', os.getenv('SUPABASE_URL'))
print('Key exists:', bool(os.getenv('SUPABASE_ANON_KEY')))
client = get_supabase_client()
print('Client:', client)
"
```

### Problem 2: "Invalid login credentials" Error

**Error message:**
```
❌ Invalid login credentials
```

**Solutions:**
1. Double-check email and password with team lead
2. Make sure account was created by admin
3. Try password reset (if enabled)

### Problem 3: Empty Database / No Data

**Issue**: You can login but see no papers or settings

**Explanation**: This might be normal if:
- This is your first time logging in
- Team hasn't saved any papers yet
- You're looking at a different user's data

**Solution**:
```bash
# Check if you can see users table (as admin)
python -c "
from services.supabase_client import get_supabase_admin_client
client = get_supabase_admin_client()
result = client.table('user_profiles').select('email, role').execute()
print('Users:', result.data)
"
```

### Problem 4: "Module not found" Errors

**Error message:**
```
ModuleNotFoundError: No module named 'supabase'
```

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Verify supabase package
pip show supabase
```

### Problem 5: Port Already in Use

**Error message:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Option 1: Kill the process using port 8501
lsof -ti:8501 | xargs kill -9

# Option 2: Use a different port
streamlit run app.py --server.port 8502
```

---

## Getting Help

### Before Asking for Help

1. ✅ Check this guide again
2. ✅ Read error messages carefully
3. ✅ Try the troubleshooting steps
4. ✅ Search error message online

### When Asking for Help

**Include:**
1. **Error message** (copy-paste full error)
2. **What you tried** (steps you followed)
3. **Your environment**:
   ```bash
   python --version
   pip list | grep supabase
   ls -la .env  # (don't share contents!)
   ```

### Useful Resources

- **Supabase Docs**: https://supabase.com/docs
- **Supabase Python Client**: https://supabase.com/docs/reference/python
- **Project PRD**: `docs/PRD_Supabase_Integration.md`
- **Project Owner**: Your project owner (ask in Slack/Discord/etc.)

---

## Quick Reference: Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate  # Windows

# Start the app
streamlit run app.py

# Run tests (if available)
pytest

# Update dependencies
pip install -r requirements.txt

# Check database connection
python -c "from services.supabase_client import get_supabase_client; print(get_supabase_client())"

# Create a new user (admin only)
python -m utils.admin_tools.create_admin_email

# Check git status
git status

# Pull latest changes
git pull origin main
```

---

## Security Best Practices

### DO ✅

- Keep `.env` file secure (never commit to git)
- Use strong passwords for your account
- Ask team lead for credentials via secure channel (Signal, encrypted email)
- Regularly pull latest code from git

### DON'T ❌

- Commit `.env` to git
- Share credentials in Slack/Discord/public channels
- Use the service role key in client-side code
- Create a new Supabase project for this app

---

## Next Steps After Setup

Once your setup is working:

1. **Familiarize yourself** with the codebase:
   - Read `docs/PRD_Supabase_Integration.md`
   - Explore `services/` folder (database logic)
   - Look at `components/` folder (UI components)

2. **Test basic features**:
   - Search for papers
   - Save preferences
   - Try different tabs (Papers, Models, Settings)

3. **Start contributing**:
   - Pick a task from Phase 4.2.2 (Paper Cache Migration)
   - Create a new branch: `git checkout -b feature/your-feature-name`
   - Make changes, commit, push, create PR

---

## Summary Checklist

Before you can start developing, make sure:

- [ ] Python 3.9+ installed
- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] `requirements.txt` installed
- [ ] `.env` file created with real credentials
- [ ] Supabase connection test passed
- [ ] User account created (by team lead or self-registration)
- [ ] Successfully logged into app
- [ ] Can see Settings tab and profile data

**If all boxes are checked, you're ready to develop! 🎉**

---

## Questions?

If you're stuck on any step, reach out to:
- **Project Owner**: Your project owner
- **Documentation**: `docs/` folder
- **Supabase Dashboard**: https://supabase.com/dashboard (ask project owner for access)

Good luck! 🚀
