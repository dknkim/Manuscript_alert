-- ============================================================
-- MANUSCRIPT ALERT SYSTEM - DATABASE SCHEMA
-- Email-Based Authentication (Simplified)
-- ============================================================
-- This script drops all existing tables and recreates them
-- with EMAIL as the primary login identifier

-- ============================================================
-- STEP 1: DROP ALL EXISTING TABLES
-- ============================================================

DROP TABLE IF EXISTS activity_log CASCADE;
DROP TABLE IF EXISTS project_collaborators CASCADE;
DROP TABLE IF EXISTS keyword_intelligence CASCADE;
DROP TABLE IF EXISTS user_paper_interactions CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;
DROP TABLE IF EXISTS search_alerts CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS background_jobs CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS papers CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Drop custom types
DROP TYPE IF EXISTS user_role CASCADE;
DROP TYPE IF EXISTS notification_type CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS is_admin() CASCADE;
DROP FUNCTION IF EXISTS get_user_role(uuid) CASCADE;

-- ============================================================
-- STEP 2: CREATE ENUM TYPES
-- ============================================================

-- User roles enum
CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');

-- Notification types
CREATE TYPE notification_type AS ENUM ('paper_match', 'system', 'collaboration', 'export_ready');

-- ============================================================
-- STEP 3: CREATE TABLES
-- ============================================================

-- User profiles table - EMAIL IS PRIMARY LOGIN
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,  -- PRIMARY LOGIN - matches auth.users.email
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

-- System settings table
CREATE TABLE system_settings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  key TEXT UNIQUE NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Papers table
CREATE TABLE papers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  authors TEXT[],
  abstract TEXT,
  publication_date DATE,
  journal TEXT,
  doi TEXT,
  arxiv_id TEXT,
  pubmed_id TEXT,
  source TEXT NOT NULL,
  url TEXT,
  keywords TEXT[],
  relevance_score FLOAT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Projects table
CREATE TABLE projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  keywords TEXT[],
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Background jobs table
CREATE TABLE background_jobs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  job_type TEXT NOT NULL,
  status TEXT DEFAULT 'queued' NOT NULL,
  progress_percentage INTEGER DEFAULT 0,
  message TEXT,
  metadata JSONB DEFAULT '{}',
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  estimated_completion TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Notifications table
CREATE TABLE notifications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  type notification_type NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  link TEXT,
  is_read BOOLEAN DEFAULT FALSE NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Search alerts table
CREATE TABLE search_alerts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  keywords TEXT[] NOT NULL,
  filters JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  last_run TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Knowledge base table
CREATE TABLE knowledge_base (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  document_name TEXT NOT NULL,
  document_type TEXT,
  file_path TEXT,
  file_url TEXT,
  file_size BIGINT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- User paper interactions table
CREATE TABLE user_paper_interactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  paper_id UUID REFERENCES papers(id) ON DELETE CASCADE NOT NULL,
  interaction_type TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  UNIQUE(user_id, paper_id, interaction_type)
);

-- Keyword intelligence table
CREATE TABLE keyword_intelligence (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  keyword TEXT UNIQUE NOT NULL,
  base_score FLOAT DEFAULT 1.0,
  journal_scores JSONB DEFAULT '{}',
  source_scores JSONB DEFAULT '{}',
  topic_relevance JSONB DEFAULT '{}',
  frequency_count INTEGER DEFAULT 1,
  last_seen TIMESTAMP DEFAULT NOW(),
  trending_score FLOAT DEFAULT 0.0,
  user_interaction_score FLOAT DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Project collaborators table (for future multi-user)
CREATE TABLE project_collaborators (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role TEXT DEFAULT 'viewer' NOT NULL,
  added_at TIMESTAMP DEFAULT NOW() NOT NULL,
  added_by UUID REFERENCES auth.users(id),
  UNIQUE(project_id, user_id)
);

-- Activity log table
CREATE TABLE activity_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id UUID,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- ============================================================
-- STEP 4: CREATE INDEXES
-- ============================================================

-- User profiles indexes
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);

-- Papers indexes
CREATE INDEX idx_papers_user_id ON papers(user_id);
CREATE INDEX idx_papers_publication_date ON papers(publication_date DESC);
CREATE INDEX idx_papers_source ON papers(source);

-- Projects indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_is_active ON projects(is_active);

-- Background jobs indexes
CREATE INDEX idx_background_jobs_user_status ON background_jobs(user_id, status);
CREATE INDEX idx_background_jobs_created_at ON background_jobs(created_at DESC);

-- Notifications indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- Activity log indexes
CREATE INDEX idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at DESC);

-- ============================================================
-- STEP 5: CREATE HELPER FUNCTIONS
-- ============================================================

-- Function to check if current user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM user_profiles
    WHERE id = auth.uid()
    AND role = 'admin'
    AND is_active = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user role
CREATE OR REPLACE FUNCTION get_user_role(user_uuid UUID)
RETURNS user_role AS $$
  SELECT role FROM user_profiles WHERE id = user_uuid AND is_active = TRUE;
$$ LANGUAGE sql SECURITY DEFINER;

-- ============================================================
-- STEP 6: ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_paper_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE keyword_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_collaborators ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- User Profiles Policies
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles"
  ON user_profiles FOR SELECT
  USING (is_admin());

CREATE POLICY "Admins can create profiles"
  ON user_profiles FOR INSERT
  WITH CHECK (is_admin());

CREATE POLICY "Admins can update all profiles"
  ON user_profiles FOR UPDATE
  USING (is_admin());

-- Papers Policies
CREATE POLICY "Users can view own papers"
  ON papers FOR ALL
  USING (auth.uid() = user_id);

-- Projects Policies
CREATE POLICY "Users can manage own projects"
  ON projects FOR ALL
  USING (auth.uid() = user_id);

-- Background Jobs Policies
CREATE POLICY "Users can view own jobs"
  ON background_jobs FOR ALL
  USING (auth.uid() = user_id);

-- Notifications Policies
CREATE POLICY "Users can view own notifications"
  ON notifications FOR ALL
  USING (auth.uid() = user_id);

-- Search Alerts Policies
CREATE POLICY "Users can manage own alerts"
  ON search_alerts FOR ALL
  USING (auth.uid() = user_id);

-- Knowledge Base Policies
CREATE POLICY "Users can manage own knowledge base"
  ON knowledge_base FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = knowledge_base.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- User Paper Interactions Policies
CREATE POLICY "Users can manage own interactions"
  ON user_paper_interactions FOR ALL
  USING (auth.uid() = user_id);

-- Keyword Intelligence Policies (read-only for all authenticated users)
CREATE POLICY "Authenticated users can view keyword intelligence"
  ON keyword_intelligence FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage keyword intelligence"
  ON keyword_intelligence FOR ALL
  USING (is_admin());

-- Project Collaborators Policies
CREATE POLICY "Users can view collaborations they're part of"
  ON project_collaborators FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Project owners can manage collaborators"
  ON project_collaborators FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = project_collaborators.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Activity Log Policies
CREATE POLICY "Users can view own activity"
  ON activity_log FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins can view all activity"
  ON activity_log FOR SELECT
  USING (is_admin());

CREATE POLICY "All authenticated users can insert activity"
  ON activity_log FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- System Settings Policies
CREATE POLICY "All authenticated users can view settings"
  ON system_settings FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage settings"
  ON system_settings FOR ALL
  USING (is_admin());

-- ============================================================
-- STEP 7: INSERT DEFAULT SYSTEM SETTINGS
-- ============================================================

INSERT INTO system_settings (key, value, description) VALUES
  ('default_search_limit', '1000', 'Default number of papers to fetch per source'),
  ('refresh_interval_hours', '24', 'How often to refresh paper data (hours)'),
  ('min_keywords_match', '2', 'Minimum number of keywords that must match for relevance'),
  ('enable_background_jobs', 'true', 'Enable background processing for paper fetching');

-- ============================================================
-- COMPLETE!
-- ============================================================
