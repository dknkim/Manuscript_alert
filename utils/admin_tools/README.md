# Admin Tools

Utilities for managing users and admin accounts.

## Scripts

### `promote_to_admin.py`
Promote an existing user to admin role.

**Usage:**
```bash
python utils/admin_tools/promote_to_admin.py
```

**Use when:** Your co-author signed up as regular user and needs admin access.

---

### `list_users.py`
List all users with their roles and status.

**Usage:**
```bash
python utils/admin_tools/list_users.py
```

**Shows:**
- Email
- Role (admin/user/guest)
- Full name
- Active status
- Last login
- Created date

---

### `create_admin_email.py`
Create a new admin user from scratch.

**Usage:**
```bash
python utils/admin_tools/create_admin_email.py
```

**Use when:** Creating the first admin or adding a new admin directly.

---

## Typical Workflow

**For adding co-author as admin:**

1. Co-author signs up via app (becomes regular user)
2. You run: `python utils/admin_tools/promote_to_admin.py`
3. Enter their email
4. They're now admin!

**To see all users:**
```bash
python utils/admin_tools/list_users.py
```

---

## Requirements

All scripts require:
- `.env` file with `SUPABASE_SERVICE_ROLE_KEY`
- Python packages: `supabase`, `python-dotenv`

See [docs/USER_GUIDE.md](../../docs/USER_GUIDE.md) for full documentation.
