-- ============================================================
-- USER PREFERENCES TABLE MIGRATION
-- ============================================================
-- Refactor preferences from JSONB blob to structured table
-- Benefits: Better querying, type safety, indexing, admin UI support
--
-- Date: October 27, 2025
-- ============================================================

-- Create user_preferences table with structured columns
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,

  -- UI Preferences
  theme TEXT DEFAULT 'light' NOT NULL CHECK (theme IN ('light', 'dark')),
  notifications_enabled BOOLEAN DEFAULT true NOT NULL,
  email_alerts BOOLEAN DEFAULT false NOT NULL,

  -- Research Keywords (array for better querying and indexing)
  keywords TEXT[] DEFAULT ARRAY[
    'Alzheimer''s disease',
    'PET',
    'amyloid',
    'tau',
    'plasma',
    'brain'
  ] NOT NULL,

  -- Journal Settings (JSONB for complex nested structures)
  target_journals JSONB DEFAULT '{
    "exact_matches": ["jama", "nature", "science", "radiology", "ajnr", "the lancet"],
    "family_matches": ["jama", "nature", "science", "npj", "the lancet"],
    "specific_journals": [
      "american journal of neuroradiology",
      "alzheimer''s & dementia",
      "alzheimers dement",
      "ebiomedicine",
      "journal of magnetic resonance imaging",
      "magnetic resonance in medicine",
      "radiology",
      "jmri",
      "j magn reson imaging",
      "brain : a journal of neurology"
    ]
  }'::jsonb NOT NULL,

  journal_exclusions TEXT[] DEFAULT ARRAY[
    'abdominal',
    'pediatric',
    'cardiovascular and interventional',
    'interventional',
    'skeletal',
    'clinical',
    'academic',
    'investigative',
    'case reports',
    'oral surgery',
    'korean journal of',
    'the neuroradiology',
    'japanese journal of',
    'brain research',
    'brain and behavior',
    'brain imaging and behavior',
    'brain stimulation',
    'brain and cognition',
    'brain, behavior, and immunity',
    'metabolic brain disease',
    'neuroscience letters',
    'neuroscience bulletin',
    'neuroscience methods',
    'neuroscience research',
    'neuroscience and biobehavioral',
    'clinical neuroscience',
    'neuropsychiatry',
    'ibro neuroscience',
    'acs chemical neuroscience',
    'proceedings of the national academy',
    'life science alliance',
    'life sciences',
    'animal science',
    'veterinary medical science',
    'philosophical transactions',
    'annals of the new york academy'
  ] NOT NULL,

  journal_scoring JSONB DEFAULT '{
    "enabled": true,
    "high_impact_journal_boost": {
      "5_or_more_keywords": 4.9,
      "4_keywords": 3.7,
      "3_keywords": 2.8,
      "2_keywords": 1.0,
      "1_keyword": 0.1
    }
  }'::jsonb NOT NULL,

  -- Keyword Scoring (JSONB for nested structure)
  keyword_scoring JSONB DEFAULT '{
    "high_priority": {
      "keywords": ["Alzheimer''s disease", "amyloid"],
      "boost": 1.5
    },
    "medium_priority": {
      "keywords": ["PET", "brain", "plasma"],
      "boost": 1.2
    }
  }'::jsonb NOT NULL,

  -- Search Settings (individual columns for better querying)
  search_days_back INTEGER DEFAULT 8 NOT NULL CHECK (search_days_back > 0 AND search_days_back <= 30),
  search_mode TEXT DEFAULT 'Brief' NOT NULL CHECK (search_mode IN ('Brief', 'Standard', 'Extended')),
  min_keyword_matches INTEGER DEFAULT 2 NOT NULL CHECK (min_keyword_matches >= 1),
  max_results_display INTEGER DEFAULT 50 NOT NULL CHECK (max_results_display >= 10),

  -- Default Sources (boolean columns for easy querying)
  default_source_pubmed BOOLEAN DEFAULT true NOT NULL,
  default_source_arxiv BOOLEAN DEFAULT false NOT NULL,
  default_source_biorxiv BOOLEAN DEFAULT true NOT NULL,
  default_source_medrxiv BOOLEAN DEFAULT true NOT NULL,

  journal_quality_filter BOOLEAN DEFAULT false NOT NULL,

  -- UI Display Settings
  show_abstracts BOOLEAN DEFAULT true NOT NULL,
  show_keywords BOOLEAN DEFAULT true NOT NULL,
  show_relevance_scores BOOLEAN DEFAULT true NOT NULL,
  papers_per_page INTEGER DEFAULT 50 NOT NULL CHECK (papers_per_page >= 10 AND papers_per_page <= 200),

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Primary lookup index
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- GIN index for keywords array (enables fast array operations)
CREATE INDEX IF NOT EXISTS idx_user_preferences_keywords ON user_preferences USING GIN(keywords);

-- Index for common query patterns
CREATE INDEX IF NOT EXISTS idx_user_preferences_search_mode ON user_preferences(search_mode);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Users can read their own preferences
CREATE POLICY "Users can view own preferences"
  ON user_preferences FOR SELECT
  USING (auth.uid() = user_id);

-- Users can update their own preferences
CREATE POLICY "Users can update own preferences"
  ON user_preferences FOR UPDATE
  USING (auth.uid() = user_id);

-- Admins can view all preferences (for admin UI)
CREATE POLICY "Admins can view all preferences"
  ON user_preferences FOR SELECT
  USING (is_admin());

-- Admins can update all preferences (for admin user management)
CREATE POLICY "Admins can update all preferences"
  ON user_preferences FOR UPDATE
  USING (is_admin());

-- System can insert preferences (for new user creation)
CREATE POLICY "System can insert preferences"
  ON user_preferences FOR INSERT
  WITH CHECK (true);

-- ============================================================
-- TRIGGER: Auto-create preferences on user signup
-- ============================================================

CREATE OR REPLACE FUNCTION create_default_user_preferences()
RETURNS TRIGGER AS $$
BEGIN
  -- Create default preferences for new user
  INSERT INTO user_preferences (user_id)
  VALUES (NEW.id);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach trigger to user_profiles table
CREATE TRIGGER on_user_created_create_preferences
  AFTER INSERT ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION create_default_user_preferences();

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE user_preferences IS 'Structured user preferences table - replaces user_profiles.preferences JSONB blob';
COMMENT ON COLUMN user_preferences.keywords IS 'Research keywords array - indexed with GIN for fast searches';
COMMENT ON COLUMN user_preferences.search_mode IS 'Paper search depth: Brief (fast), Standard (balanced), Extended (comprehensive)';
COMMENT ON COLUMN user_preferences.journal_scoring IS 'JSONB structure for dynamic journal relevance scoring';
