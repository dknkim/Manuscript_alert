-- =============================================================================
-- DROP ALL TABLES AND RECREATE WITH USERNAME-FIRST AUTHENTICATION
-- =============================================================================
-- WARNING: This will DELETE ALL DATA in your database!
-- Only run this if you're starting fresh with no data to preserve
-- =============================================================================

-- PART 1: DROP ALL EXISTING TABLES AND TYPES
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS activity_log CASCADE;
DROP TABLE IF EXISTS user_paper_interactions CASCADE;
DROP TABLE IF EXISTS keyword_intelligence CASCADE;
DROP TABLE IF EXISTS search_alerts CASCADE;
DROP TABLE IF EXISTS paper_collections CASCADE;
DROP TABLE IF EXISTS papers CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;
DROP TABLE IF EXISTS project_collaborators CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS background_jobs CASCADE;

-- Drop types
DROP TYPE IF EXISTS user_role CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS is_admin() CASCADE;
DROP FUNCTION IF EXISTS get_user_role() CASCADE;
DROP FUNCTION IF EXISTS check_username_unique() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS handle_new_user() CASCADE;

-- =============================================================================
-- PART 2: CREATE NEW SCHEMA - USERNAME-FIRST AUTHENTICATION
-- =============================================================================

-- User roles enum
CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');

-- User profiles - USERNAME is the primary login identifier
-- Email is OPTIONAL and only for recovery/notifications
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,  -- PRIMARY LOGIN - REQUIRED
  email TEXT UNIQUE,  -- OPTIONAL - for recovery/notifications only
  full_name TEXT,
  role user_role DEFAULT 'user' NOT NULL,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  preferences JSONB DEFAULT '{
    "theme": "light",
    "notifications_enabled": true,
    "email_alerts": false
  }',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
  last_login TIMESTAMP,
  created_by UUID REFERENCES auth.users(id)
);

-- Indexes for user_profiles
CREATE INDEX idx_user_profiles_username ON user_profiles(username) WHERE is_active = TRUE;
CREATE INDEX idx_user_profiles_role ON user_profiles(role) WHERE is_active = TRUE;

-- Comments for clarity
COMMENT ON TABLE user_profiles IS 'User authentication is USERNAME + PASSWORD. Email is optional for notifications/recovery.';
COMMENT ON COLUMN user_profiles.username IS 'PRIMARY login identifier (REQUIRED) - users login with this, not email';
COMMENT ON COLUMN user_profiles.email IS 'OPTIONAL - only for password recovery and notifications';
COMMENT ON COLUMN user_profiles.role IS 'admin = full control, user = standard access, guest = read-only';

-- System settings (admin-only configuration)
CREATE TABLE system_settings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  updated_by UUID REFERENCES auth.users(id),
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Research projects
CREATE TABLE projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  is_public BOOLEAN DEFAULT FALSE NOT NULL,
  keywords TEXT[] DEFAULT '{}',
  sources TEXT[] DEFAULT ARRAY['pubmed', 'arxiv', 'biorxiv', 'medrxiv'],
  settings JSONB DEFAULT '{
    "auto_fetch": true,
    "fetch_frequency": "daily",
    "relevance_threshold": 0.5
  }',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Project collaborators (future multi-user)
CREATE TABLE project_collaborators (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role TEXT CHECK (role IN ('owner', 'editor', 'viewer')) NOT NULL,
  added_by UUID REFERENCES auth.users(id),
  added_at TIMESTAMP DEFAULT NOW() NOT NULL,
  UNIQUE(project_id, user_id)
);

-- Papers storage
CREATE TABLE papers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  external_id TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('pubmed', 'arxiv', 'biorxiv', 'medrxiv')),
  title TEXT NOT NULL,
  authors TEXT[] DEFAULT '{}',
  abstract TEXT,
  published_date DATE,
  journal TEXT,
  doi TEXT,
  url TEXT NOT NULL,
  pdf_url TEXT,
  metadata JSONB DEFAULT '{}',
  indexed_at TIMESTAMP DEFAULT NOW() NOT NULL,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  UNIQUE(external_id, source)
);

-- Paper collections (saved papers per project)
CREATE TABLE paper_collections (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  paper_id UUID REFERENCES papers(id) ON DELETE CASCADE NOT NULL,
  relevance_score FLOAT CHECK (relevance_score >= 0 AND relevance_score <= 1),
  keywords_matched TEXT[] DEFAULT '{}',
  notes TEXT,
  is_favorite BOOLEAN DEFAULT FALSE NOT NULL,
  tags TEXT[] DEFAULT '{}',
  added_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
  UNIQUE(project_id, paper_id)
);

-- Search alerts (automated notifications)
CREATE TABLE search_alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  alert_name TEXT NOT NULL,
  keywords TEXT[] NOT NULL,
  frequency TEXT CHECK (frequency IN ('realtime', 'daily', 'weekly')) DEFAULT 'daily',
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  last_triggered TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Activity log (audit trail)
CREATE TABLE activity_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id UUID,
  metadata JSONB DEFAULT '{}',
  ip_address INET,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Background jobs tracking
CREATE TABLE background_jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
  progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
  message TEXT,
  metadata JSONB DEFAULT '{}',
  started_at TIMESTAMP DEFAULT NOW() NOT NULL,
  completed_at TIMESTAMP,
  estimated_completion TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- =============================================================================
-- PART 3: INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX idx_papers_source_date ON papers(source, published_date DESC);
CREATE INDEX idx_papers_external_id ON papers(external_id);
CREATE INDEX idx_paper_collections_project ON paper_collections(project_id);
CREATE INDEX idx_paper_collections_favorite ON paper_collections(project_id, is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_activity_log_user ON activity_log(user_id, created_at DESC);
CREATE INDEX idx_background_jobs_user_status ON background_jobs(user_id, status);
CREATE INDEX idx_background_jobs_created ON background_jobs(created_at DESC);

-- =============================================================================
-- PART 4: HELPER FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Helper function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM user_profiles
    WHERE id = auth.uid() AND role = 'admin' AND is_active = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper function to get user role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS user_role AS $$
BEGIN
  RETURN (
    SELECT role FROM user_profiles
    WHERE id = auth.uid() AND is_active = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Uniqueness validation for username/email updates
CREATE OR REPLACE FUNCTION check_username_unique()
RETURNS TRIGGER AS $$
BEGIN
  -- Check username uniqueness (always required)
  IF TG_OP = 'UPDATE' AND NEW.username != OLD.username THEN
    IF EXISTS (
      SELECT 1 FROM user_profiles
      WHERE username = NEW.username AND id != NEW.id
    ) THEN
      RAISE EXCEPTION 'Username "%" is already taken', NEW.username
        USING ERRCODE = '23505';
    END IF;
  END IF;

  -- Check email uniqueness (only if provided)
  IF NEW.email IS NOT NULL THEN
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.email != OLD.email) THEN
      IF EXISTS (
        SELECT 1 FROM user_profiles
        WHERE email = NEW.email AND id != NEW.id
      ) THEN
        RAISE EXCEPTION 'Email "%" is already registered', NEW.email
          USING ERRCODE = '23505';
      END IF;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PART 5: TRIGGERS
-- =============================================================================

-- Triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_paper_collections_updated_at
  BEFORE UPDATE ON paper_collections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Uniqueness validation trigger
CREATE TRIGGER check_user_uniqueness
  BEFORE INSERT OR UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION check_username_unique();

-- =============================================================================
-- PART 6: ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_collaborators ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE paper_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;

-- USER PROFILES POLICIES
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
  ON user_profiles FOR SELECT
  USING (is_admin());

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (
    auth.uid() = id AND
    role = (SELECT role FROM user_profiles WHERE id = auth.uid())
  );

CREATE POLICY "System can create user profiles"
  ON user_profiles FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Admins can manage all profiles"
  ON user_profiles FOR ALL
  USING (is_admin())
  WITH CHECK (is_admin());

-- SYSTEM SETTINGS POLICIES
CREATE POLICY "Admins manage system settings"
  ON system_settings FOR ALL
  USING (is_admin())
  WITH CHECK (is_admin());

CREATE POLICY "Users can view system settings"
  ON system_settings FOR SELECT
  USING (auth.role() = 'authenticated');

-- PROJECTS POLICIES
CREATE POLICY "Users can view own projects"
  ON projects FOR SELECT
  USING (owner_id = auth.uid());

CREATE POLICY "Users can view public projects"
  ON projects FOR SELECT
  USING (is_public = TRUE);

CREATE POLICY "Admins can view all projects"
  ON projects FOR SELECT
  USING (is_admin());

CREATE POLICY "Users can manage own projects"
  ON projects FOR ALL
  USING (owner_id = auth.uid())
  WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Admins can manage all projects"
  ON projects FOR ALL
  USING (is_admin())
  WITH CHECK (is_admin());

-- PAPERS POLICIES
CREATE POLICY "Authenticated users can view papers"
  ON papers FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can insert papers"
  ON papers FOR INSERT
  WITH CHECK (is_admin());

-- PAPER COLLECTIONS POLICIES
CREATE POLICY "Users can view own collections"
  ON paper_collections FOR SELECT
  USING (
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Admins can view all collections"
  ON paper_collections FOR SELECT
  USING (is_admin());

CREATE POLICY "Users can manage own collections"
  ON paper_collections FOR ALL
  USING (
    get_user_role() != 'guest' AND
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  )
  WITH CHECK (
    get_user_role() != 'guest' AND
    project_id IN (
      SELECT id FROM projects WHERE owner_id = auth.uid()
    )
  );

-- SEARCH ALERTS POLICIES
CREATE POLICY "Users can manage own alerts"
  ON search_alerts FOR ALL
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid() AND get_user_role() != 'guest');

CREATE POLICY "Admins can manage all alerts"
  ON search_alerts FOR ALL
  USING (is_admin())
  WITH CHECK (is_admin());

-- ACTIVITY LOG POLICIES
CREATE POLICY "Admins can view activity logs"
  ON activity_log FOR SELECT
  USING (is_admin());

CREATE POLICY "Users can view own activity"
  ON activity_log FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "System can insert logs"
  ON activity_log FOR INSERT
  WITH CHECK (true);

-- BACKGROUND JOBS POLICIES
CREATE POLICY "Users can view own jobs"
  ON background_jobs FOR ALL
  USING (auth.uid() = user_id);

-- =============================================================================
-- PART 7: INSERT DEFAULT SYSTEM SETTINGS
-- =============================================================================
INSERT INTO system_settings (key, value, description)
VALUES
  ('default_sources', '["pubmed", "arxiv", "biorxiv", "medrxiv"]', 'Default paper sources for new projects'),
  ('max_users', '10', 'Maximum number of users allowed'),
  ('guest_access_enabled', 'true', 'Allow guest user registration'),
  ('fetch_schedule', '{"hour": 2, "minute": 0}', 'Daily paper fetch schedule (UTC)');

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these to verify the setup

-- Check that all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check user_profiles structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles'
ORDER BY ordinal_position;

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
