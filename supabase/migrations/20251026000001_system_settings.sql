-- Insert default system settings
INSERT INTO system_settings (key, value, description)
VALUES
  ('default_sources', '["pubmed", "arxiv", "biorxiv", "medrxiv"]', 'Default paper sources for new projects'),
  ('max_users', '10', 'Maximum number of users allowed'),
  ('guest_access_enabled', 'true', 'Allow guest user registration'),
  ('fetch_schedule', '{"hour": 2, "minute": 0}', 'Daily paper fetch schedule (UTC)')
ON CONFLICT (key) DO NOTHING;

-- Verify
SELECT key, value, description FROM system_settings ORDER BY key;
