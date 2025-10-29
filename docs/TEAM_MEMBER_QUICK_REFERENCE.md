# Quick Reference for Team Members - Connecting to Project Owner's Supabase

## 🎯 The Setup (What's Different Now)

**Before**: You created the Supabase project, project owner connects to yours
**Now**: Project owner creates Supabase project, YOU connect to theirs

### Why This Change?
- Project owner's Supabase account will be the **deployment server**
- Both of you work on the same database
- Project owner is "Project Owner", you are "Team Member"

---

## 📋 What You Need FROM Your Project Owner

Ask them to send you (via **Signal** or **1Password**, NOT email/Slack):

### 1. Three Supabase Credentials

```
SUPABASE_URL=https://[their-project-id].supabase.co
SUPABASE_ANON_KEY=eyJhbGci... (long JWT token)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (different JWT token)
```

**Where they find these:**
- Login to https://supabase.com/dashboard
- Go to: `Project Settings` → `API`
- Copy all 3 values

### 2. Your User Account

They should create an admin account for you:

```bash
# On their machine:
python -m utils.admin_tools.create_admin_email

# They enter:
Email: your.email@example.com
Full Name: Your Name
Role: admin
Password: <temporary-password>
```

**They send you:**
```
Email: your.email@example.com
Password: <temp-password>
```

---

## 🚀 Your Setup Steps (Once You Have Credentials)

### Step 1: Update Your `.env` File

```bash
# Edit your .env
nano .env

# Paste their credentials:
SUPABASE_URL=https://[their-project-id].supabase.co
SUPABASE_ANON_KEY=[their-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[their-service-role-key]
```

### Step 2: Test Connection

```bash
python -c "from services.supabase_client import get_supabase_client; print('✅ Connected!' if get_supabase_client() else '❌ Failed')"
```

**Expected**: `✅ Connected!`

### Step 3: Start App

```bash
streamlit run app.py
```

### Step 4: Login

- Open http://localhost:8501
- Enter: your email + temporary password (from project owner)
- Go to Settings → My Profile → Change Password
- Set your own password

### Step 5: Verify Everything Works

```
✓ Can you see Settings → My Profile?
✓ Can you edit your name and save?
✓ Can you go to Papers tab?
✓ Can you search for papers?
```

If all YES → You're good! 🎉

---

## 📤 What to Send Your Project Owner

### Documents to Share

Send them:
1. **Repository access** (if private repo)
2. **[docs/SETUP_GUIDE_FOR_DEVELOPERS.md](./SETUP_GUIDE_FOR_DEVELOPERS.md)** - Complete setup guide
3. **[docs/CREDENTIALS_TO_SHARE.md](./CREDENTIALS_TO_SHARE.md)** - What they need to do

### Quick Checklist for Them

**Project Owner Setup Checklist (send this):**

```
□ Step 1: Create Supabase account at https://supabase.com
□ Step 2: Create new project (name: "Manuscript Alert Production")
□ Step 3: Get API keys (Settings → API)
□ Step 4: Clone repo: git clone [repo-url]
□ Step 5: Install dependencies: pip install -r requirements.txt
□ Step 6: Create .env with your Supabase credentials
□ Step 7: Run migrations: supabase db push
         OR manually via SQL Editor:
         - Run: supabase/migrations/20251027000000_email_based_auth.sql
         - Run: supabase/migrations/20251027000001_user_preferences_table.sql
□ Step 8: Create your admin account: python -m utils.admin_tools.create_admin_email
□ Step 9: Create team member's account (their email, role: admin)
□ Step 10: Share credentials with team member via Signal/1Password:
         - SUPABASE_URL
         - SUPABASE_ANON_KEY
         - SUPABASE_SERVICE_ROLE_KEY
         - Team member's login: email + temp password
```

---

## 🔐 MCP Setup (If Using Claude Desktop)

Once you have their credentials, update your MCP config:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--supabase-url", "https://[their-project-id].supabase.co",
        "--supabase-key", "[their-anon-key]"
      ]
    }
  }
}
```

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)

---

## 🤝 Working Together

### Database is Shared

```
Project Owner's Supabase Project
┌─────────────────────────┐
│                         │
│  Users:                 │
│  - Project owner (admin) │
│  - Team member (admin)  │
│                         │
│  Papers: (shared)       │
│  Settings: (per-user)   │
│                         │
└─────────────────────────┘
     ↑              ↑
     │              │
Project Owner   Team Member
```

### What's Shared vs. Individual

**Shared (everyone sees same data)**:
- Papers table
- Projects table
- User list (in Admin tab)

**Individual (per-user)**:
- Your preferences (keywords, settings)
- Your profile (name, password)
- Your saved papers/bookmarks

### Making Changes

**Database changes** (migrations):
1. Create migration file in `supabase/migrations/`
2. Test locally on your machine
3. Push to git
4. Project owner runs: `supabase db push`
5. Changes apply to production database

**Code changes**:
1. Create branch: `git checkout -b feature/your-feature`
2. Make changes, test locally
3. Commit, push, create PR
4. Project owner reviews and merges
5. Both pull latest: `git pull origin main`

---

## ⚠️ Important Reminders

### Security
- ✅ Keep `.env` secure (never commit to git)
- ✅ Share credentials via Signal/1Password only
- ✅ Use different passwords for different services
- ❌ Don't share `SERVICE_ROLE_KEY` publicly
- ❌ Don't commit credentials to git

### Database Safety
- ⚠️ Both of you can modify the database
- ⚠️ Always test migrations locally first
- ⚠️ Use pre-commit hooks (already setup)
- ⚠️ Never run `DROP TABLE` in production

### Development Workflow
1. Always `git pull` before starting work
2. Create feature branches (not main)
3. Test locally before pushing
4. Communicate about database changes
5. Use the todo list to track progress

---

## 🆘 Troubleshooting

### "Connection failed"
```bash
# Check .env exists and has values
cat .env

# Verify credentials are correct
# (compare with what project owner sent you)
```

### "Invalid login credentials"
```bash
# Double-check email and password
# Make sure project owner created your account
# Try password reset (Settings → My Profile)
```

### "Module not found"
```bash
# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Kill process on port 8501
lsof -ti:8501 | xargs kill -9

# Or use different port
streamlit run app.py --server.port 8502
```

---

## 📚 Documentation Files

All documentation is in `docs/`:

- **[SETUP_GUIDE_FOR_DEVELOPERS.md](./SETUP_GUIDE_FOR_DEVELOPERS.md)** - Full setup guide (50+ pages)
- **[CREDENTIALS_TO_SHARE.md](./CREDENTIALS_TO_SHARE.md)** - What project owner needs to share
- **[PRD_Supabase_Integration.md](./PRD_Supabase_Integration.md)** - Project requirements and architecture
- **[TEAM_MEMBER_QUICK_REFERENCE.md](./TEAM_MEMBER_QUICK_REFERENCE.md)** - This file!

---

## ✅ Ready Checklist

Before you start working:

```
□ Received 3 Supabase credentials from project owner
□ Updated .env with their credentials
□ Connection test passes
□ Can login to app
□ Can see Settings → My Profile
□ Changed password from temporary to personal
□ Pulled latest code: git pull origin main
□ Virtual environment activated: source venv/bin/activate
```

**All checked?** → You're ready to collaborate! 🚀

---

## 🎯 Next Steps

1. **Verify setup** - Make sure everything works
2. **Review PRD** - Read `docs/PRD_Supabase_Integration.md`
3. **Pick a task** - Start with Phase 4.2.2 (Paper Cache Migration)
4. **Coordinate** - Discuss with project owner who does what
5. **Start coding!** - Create feature branch and start implementing

---

## 💬 Questions?

If you get stuck:
1. Check troubleshooting section above
2. Read full setup guide: `docs/SETUP_GUIDE_FOR_DEVELOPERS.md`
3. Ask project owner (they're the project owner)
4. Check Supabase docs: https://supabase.com/docs

Good luck! 🎉
