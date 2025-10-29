# What Your Project Owner Needs to Share with You

## ⚠️ IMPORTANT: Role Clarification

**Your project owner** is the **Project Owner** (will host the deployment server on their Supabase account)

**You** are the **Team Member** (will connect to their Supabase project)

---

## What You Need FROM Your Project Owner

### 1. Repository Access (if applicable)
- Git repository URL
- Collaborator invite (if private repo)

### 2. Supabase Credentials (CRITICAL - via secure channel)

**Ask your project owner to send these via encrypted message (Signal, 1Password, etc.):**

```
SUPABASE_URL: https://[their-project-id].supabase.co
SUPABASE_ANON_KEY: eyJhbGci... (long string)
SUPABASE_SERVICE_ROLE_KEY: eyJhbGci... (different long string)
```

**Where they find these:**
1. Login to https://supabase.com/dashboard
2. Go to: Project Settings → API
3. Copy the 3 values above

**⚠️ Security Note**:
- `ANON_KEY` is safe-ish (used in client apps)
- `SERVICE_ROLE_KEY` is ADMIN access - keep it secret!
- Use encrypted messaging (NOT Slack, NOT email)

### 3. Your User Account

**Ask your project owner to create an account for you:**

They should run:
```bash
python -m utils.admin_tools.create_admin_email
```

And enter:
- **Email**: `your.email@example.com` (your preferred email)
- **Full Name**: `Your Name`
- **Role**: `admin` (you need admin access)
- **Password**: (they create a temporary one)

**They send you:**
```
Email: your.email@example.com
Temporary Password: <temp-password>
```

**Then you:**
1. Login to the app
2. Go to Settings → My Profile → Change Password
3. Set your own password

---

## Quick Setup Steps for Team Members

Once you receive the 3 credentials from your project owner:

### 1. Update Your `.env` File

```bash
# Edit your .env file
nano .env

# Replace with project owner's credentials:
SUPABASE_URL=https://[their-project-id].supabase.co
SUPABASE_ANON_KEY=[their-anon-key]
SUPABASE_SERVICE_ROLE_KEY=[their-service-role-key]
```

### 2. Test Connection

```bash
python -c "from services.supabase_client import get_supabase_client; print('✅ Connected!' if get_supabase_client() else '❌ Failed')"
```

### 3. Start the App

```bash
streamlit run app.py
```

### 4. Login

- Use email + password from project owner
- Change your password in Settings

### 5. Verify

- Check Settings → My Profile
- Verify you can see/edit preferences
- Test creating papers, etc.

---

## What Your Project Owner Needs to Do

### Step-by-Step for Project Owner (Your Project Owner)

**Send them this checklist:**

#### 1. Create Supabase Account
```
□ Go to https://supabase.com
□ Sign up with GitHub or email
□ Verify email
```

#### 2. Create New Project
```
□ Click "New Project"
□ Name: "Manuscript Alert Production"
□ Choose region (closest to you)
□ Select Free tier
□ Wait ~2 minutes for provisioning
```

#### 3. Get API Keys
```
□ Go to Project Settings → API
□ Copy: Project URL
□ Copy: anon public key
□ Copy: service_role key
□ Save these securely
```

#### 4. Set Up Database
```
□ Install Supabase CLI: npm install -g supabase
□ Login: supabase login
□ Link project: supabase link --project-ref [project-id]
□ Push migrations: supabase db push

OR manually via SQL Editor:
□ Run: supabase/migrations/20251027000000_email_based_auth.sql
□ Run: supabase/migrations/20251027000001_user_preferences_table.sql
```

#### 5. Create Your Admin Account
```bash
□ Run: python -m utils.admin_tools.create_admin_email
□ Enter your email, name, role=admin, password
```

#### 6. Create Team Member's Account
```bash
□ Run: python -m utils.admin_tools.create_admin_email
□ Email: their.email@example.com
□ Full Name: Their Name
□ Role: admin
□ Password: (create temporary password)
```

#### 7. Share with Team Member (via secure channel)
```
□ Send SUPABASE_URL
□ Send SUPABASE_ANON_KEY
□ Send SUPABASE_SERVICE_ROLE_KEY
□ Send team member's login credentials
```

---

## Security Best Practices

### DO ✅
- Use encrypted messaging (Signal, ProtonMail, 1Password, etc.)
- Verify recipient before sharing credentials
- Change passwords after first login
- Keep `.env` file secure (never commit to git)

### DON'T ❌
- Share credentials via Slack, Discord, SMS, or regular email
- Commit credentials to git
- Share `SERVICE_ROLE_KEY` publicly
- Reuse passwords across systems

---

## For MCP (Model Context Protocol) Users

If your project owner uses Claude Desktop or similar MCP clients:

**They need:**
1. `SUPABASE_URL`: `https://lrlefufmpvxhfumbtuwc.supabase.co`
2. `SUPABASE_ANON_KEY`: (the public key from `.env`)
3. Their user account: Email + password

**MCP Config Example:**
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--supabase-url", "https://lrlefufmpvxhfumbtuwc.supabase.co",
        "--supabase-key", "<SUPABASE_ANON_KEY>"
      ]
    }
  }
}
```

---

## What They DON'T Need

❌ They DON'T need to:
- Create a new Supabase account
- Create a new Supabase project
- Run database migrations (already done)
- Set up database schema (already done)

✅ They just need:
- Credentials to connect to YOUR existing Supabase project
- A user account in the app
- Local development setup (Python, dependencies)

---

## Template Message to Send

**Subject: Manuscript Alert System - Setup Instructions**

Hi [Name],

Here's what you need to get started with the Manuscript Alert System:

**1. Clone the repo:**
```
git clone <repo-url>
cd Manuscript_alert
```

**2. Follow the setup guide:**
Read `docs/SETUP_GUIDE_FOR_DEVELOPERS.md` for detailed instructions.

**3. Supabase credentials (use these in your `.env` file):**
```
SUPABASE_URL=https://lrlefufmpvxhfumbtuwc.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-key>
```

**4. Your user account:**
```
Email: your.email@gmail.com
Temporary Password: <temp-password>
```

**Important:**
- Change your password after first login
- Never commit `.env` to git
- Ask me if you have any setup issues

The setup guide has step-by-step instructions. Let me know when you're ready to start!

Best,
[Your Name]

---

## Quick Verification Test

After they set up, ask them to run:

```bash
# Test 1: Connection
python -c "from services.supabase_client import get_supabase_client; print('✅ Connected!' if get_supabase_client() else '❌ Failed')"

# Test 2: Login
streamlit run app.py
# They should be able to login with the credentials you gave them

# Test 3: See shared data
# In the app, go to Settings → My Profile
# They should see their profile info
```

If all 3 tests pass, they're good to go! 🎉

---

## Common Questions

**Q: Do they need Supabase dashboard access?**
A: Not required, but nice to have. You can invite them at:
https://supabase.com/dashboard/project/lrlefufmpvxhfumbtuwc/settings/team

**Q: Can they see my data?**
A: Yes, you share the same database. They'll see papers, users, etc. (based on RLS policies)

**Q: What if they lose the credentials?**
A: Just share them again via secure channel. The keys don't change unless you regenerate them.

**Q: Should we use the same user account?**
A: No! Each person should have their own account. Create separate accounts with `create_admin_email.py`

---

## Checklist Before They Start Coding

Confirm they can:
- [ ] Clone the repo
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Create `.env` with correct credentials
- [ ] Connect to Supabase (connection test passes)
- [ ] Login to the app with their account
- [ ] See their profile in Settings
- [ ] Pull latest code (`git pull`)
- [ ] Create a new branch (`git checkout -b feature/test`)

If all boxes checked → Ready to collaborate! 🚀
