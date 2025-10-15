# Settings Configuration Guide

The Manuscript Alert System now includes a comprehensive settings management system that allows you to configure keywords, journal selections, and scoring parameters through a user-friendly interface. All changes are saved directly to the source code and persist across app runs.

## Accessing Settings

1. Launch the Manuscript Alert System
2. Click on the **"⚙️ Settings"** tab
3. Navigate through the four sub-tabs to configure different aspects

## Settings Categories

### 🔍 Keywords Tab

**Research Keywords**
- Add, remove, or modify your research keywords
- Keywords are used to match papers - papers must match at least 2 keywords to be displayed
- Enter one keyword per line

**Keyword Priority Scoring**
- **High Priority Keywords**: Get a 1.5x relevance score boost
- **Medium Priority Keywords**: Get a 1.2x relevance score boost  
- **Low Priority Keywords**: Get a 1.0x relevance score boost (default)
- Select keywords from your list to assign priority levels

### 📰 Journals Tab

**Target Journals**
Configure which journals are considered high-impact and receive scoring boosts:

- **Exact Journal Matches**: Journal names that must match exactly (highest priority)
- **Journal Family Matches**: Journal name prefixes (e.g., 'nature ' for all Nature journals)
- **Specific Journal Names**: Full journal names or partial matches (lower priority)

**Journal Exclusions**
Configure patterns to exclude from target journal matching:

- **Radiology Journal Exclusions**: Patterns to exclude from radiology journals
- **Brain Journal Exclusions**: Patterns to exclude from brain journals
- Other exclusion categories are maintained automatically

### 📊 Scoring Tab

**Journal Impact Scoring**
- Enable/disable journal impact scoring
- Configure score boosts based on keyword matches:
  - 5+ keywords matched: Customizable boost (default: 5.1)
  - 4 keywords matched: Customizable boost (default: 3.7)
  - 3 keywords matched: Customizable boost (default: 2.8)
  - 2 keywords matched: Customizable boost (default: 1.3)
  - 1 keyword matched: Customizable boost (default: 0.5)

**Search Configuration**
- **Default Days Back**: Number of days to search back (1-30)
- **Default Search Mode**: Brief, Standard, or Extended
- **Minimum Keyword Matches**: Minimum keywords required for display (1-10)
- **Maximum Results Display**: Maximum papers to show (10-200)

**Default Data Sources**
- Configure which sources are enabled by default:
  - PubMed
  - arXiv
  - bioRxiv
  - medRxiv

### 💾 Backup Tab

**Automatic Backups**
- Backups are automatically created every time you save settings
- View and manage available backups
- Restore from any previous backup
- Delete old backups to save space

**Manual Backup**
- Create a manual backup at any time
- Useful before making major changes

## How Settings Persistence Works

1. **Source Code Modification**: Settings are saved by modifying the `config/settings.py` file
2. **Automatic Backups**: Before any changes, a timestamped backup is created in `config/backups/`
3. **Immediate Effect**: Changes take effect immediately when you save
4. **Persistence**: Settings remain across app restarts because they're stored in the source code

## Best Practices

### Keywords Management
- Start with broad keywords and refine based on results
- Use specific medical terms for better precision
- Group related concepts (e.g., "Alzheimer's disease" and "dementia")
- Regularly review and update based on your research focus

### Journal Configuration
- Add journals that are most relevant to your field
- Use exclusion patterns to filter out irrelevant subspecialties
- Test changes with a small date range first
- Consider the impact on paper volume when adding/removing journals

### Scoring Tuning
- Start with default values and adjust based on results
- Higher boosts make papers from target journals more prominent
- Consider the balance between precision and recall
- Monitor the relevance scores in your results

### Backup Strategy
- Create manual backups before major configuration changes
- Keep recent backups for quick rollback if needed
- Clean up old backups periodically to save space
- Test restore functionality to ensure backups work

## Troubleshooting

### Settings Not Saving
- Check file permissions in the `config/` directory
- Ensure the app has write access to the project folder
- Try creating a manual backup first

### Import Errors
- If you get import errors, check that `config/settings.py` exists
- Restore from a backup if the settings file is corrupted
- Restart the app after restoring settings

### Unexpected Behavior
- Check that your keywords don't have extra spaces or special characters
- Verify journal patterns are correctly formatted
- Use the backup system to rollback recent changes

## File Locations

- **Settings File**: `config/settings.py`
- **Backups Directory**: `config/backups/`
- **Settings Service**: `services/settings_service.py`

## Advanced Configuration

For advanced users, you can directly edit `config/settings.py` to make changes that aren't available through the UI. Always create a backup first and test your changes thoroughly.

The settings system is designed to be robust and user-friendly while providing the flexibility needed for research customization.
