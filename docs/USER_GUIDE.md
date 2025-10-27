# Manuscript Alert System - User Guide

## For New Users (Co-Authors)

### How to Register

1. **Go to the application URL** (provided by admin)

2. **You'll see the login screen**
   - Click **"Sign Up Instead"** button

3. **Fill in the signup form:**
   - **Email*** (required) - Your email address
   - **Password*** (required) - Choose a strong password (min 6 characters)
   - **Confirm Password*** (required) - Re-enter your password
   - **Full Name** (optional) - Your name for display

4. **Click "Create Account"**
   - You'll be automatically logged in
   - You'll start as a **regular user** (not admin)

5. **Start using the app!**
   - Browse papers
   - Set up your keywords
   - Configure your preferences

---

## For Admins - Managing Users

### Option 1: Create New Admin User

If you want your co-author to be an admin from the start:

```bash
python create_new_admin.py
```

Enter their:
- Email
- Password (share this with them securely)
- Full name

They can now login with full admin privileges.

---

### Option 2: Promote Existing User to Admin

If someone already registered as regular user and you want to make them admin:

```bash
python promote_to_admin.py
```

Enter their email and confirm. They'll immediately have admin access.

---

### Option 3: List All Users

To see who has access:

```bash
python list_users.py
```

Shows all users with their roles and last login times.

---

## User Roles Explained

### 🔑 **ADMIN**
- Full access to everything
- Can manage other users
- Can change system settings
- Can see all data (if implemented)

**Who should be admin:**
- Principal investigators
- Co-authors who manage the project
- Anyone who needs to add/remove users

### 👤 **USER** (Regular)
- Can use all paper search features
- Has their own preferences/keywords
- **Cannot** see other users' data (RLS enforced)
- **Cannot** create other users or change roles

**Who should be regular user:**
- Research assistants
- Lab members
- Collaborators who just need to search papers

### 👁️ **GUEST** (Read-Only)
- Currently **not implemented** in the UI
- Future feature for reviewers/advisors
- Would have view-only access

---

## Multiple Admins

**Yes, you can have multiple admins!**

Common scenarios:
- **2 co-PIs** → Both admins
- **PI + Lab Manager** → Both admins
- **Research team** → 2 admins, 5 regular users

There's no limit on number of admins.

---

## Transferring Admin Rights

If you want to hand off admin responsibilities:

1. **Promote the new admin:**
   ```bash
   python promote_to_admin.py
   ```

2. **Optional: Demote yourself to regular user:**
   - Currently requires SQL update
   - Or just keep both as admins

---

## Security Notes

- **Passwords are hashed** - Nobody can see them, not even admins
- **Each user sees only their own data** - RLS policies enforce this
- **Service role key** in `.env` - Keep this secret! It bypasses all security
- **Logout** when done on shared computers

---

## Troubleshooting

**"Email already registered"**
- That email is already in use
- Use a different email or contact admin

**"Invalid email or password"**
- Check for typos
- Passwords are case-sensitive
- Contact admin to reset password (manual process currently)

**Can't see papers/data**
- Make sure you're logged in
- Regular users only see their own data
- Ask admin if you need admin access

---

## For Developers

**Admin Scripts:**
- `create_new_admin.py` - Create admin from scratch
- `promote_to_admin.py` - Upgrade existing user
- `list_users.py` - View all users
- `create_admin_email.py` - General admin creation (with error handling)

**All scripts require:**
- `.env` file with `SUPABASE_SERVICE_ROLE_KEY`
- Python environment with `supabase` package installed
