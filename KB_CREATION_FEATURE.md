# Knowledge Base Creation Feature

## Overview

A new feature has been added to the Manuscript Alert app that allows users to create a knowledge base of today's top 20 articles with a single click.

## How to Use

1. **Open the Manuscript Alert App**: Run the app using `streamlit run app.py`

2. **Configure Your Search**: 
   - Set your keywords in the sidebar
   - Select data sources (arXiv, bioRxiv, medRxiv, PubMed)
   - Choose search mode (Brief/Standard/Extended)

3. **Create Knowledge Base**: 
   - In the sidebar, find the "🧠 Knowledge Base" section
   - Click the "📚 Create Today's KB" button
   - Wait for the process to complete (progress bar will show status)

4. **Access Your KB**: 
   - Files are saved in `./KB/` directory
   - Filename format: `knowledge_base_today_YYYYMMDD_HHMMSS.json`
   - The sidebar shows the count of existing KB files and the latest one

## Features

### ✅ **What It Does**
- Fetches papers from all selected data sources for today's date
- Ranks papers using the same relevance scoring system as the main app
- Selects the top 20 most relevant papers
- Saves in the same JSON structure as the existing knowledge base
- Shows progress with real-time status updates
- Creates the `./KB/` directory automatically if it doesn't exist

### 📊 **Progress Tracking**
- Step 1: Fetching papers from all sources (20% progress)
- Step 2: Processing and ranking papers (60% progress)  
- Step 3: Creating knowledge base file (80% progress)
- Step 4: Saving to disk (100% progress)

### 🎯 **Smart Ranking**
- Uses the same keyword matching algorithm as the main app
- Boosts scores for high-impact journals (Nature, JAMA, Science, etc.)
- Considers keyword frequency and title matches
- Ranks by relevance score to ensure quality

### 📁 **File Structure**
The created KB files follow the same structure as the existing knowledge base:

```json
{
  "metadata": {
    "created_at": "2025-09-15T20:57:47.123456",
    "weeks_covered": 1,
    "keywords_used": ["Alzheimer's disease", "PET", "MRI", ...],
    "data_sources": {"arxiv": true, "biorxiv": true, ...},
    "search_mode": "Extended",
    "total_papers": 20,
    "papers_per_week": 20,
    "date_range": "2025-09-15 to 2025-09-15"
  },
  "weeks": {
    "today": {
      "week_info": {
        "week_number": 1,
        "start_date": "2025-09-15T00:00:00",
        "end_date": "2025-09-15T00:00:00",
        "week_label": "Today (2025-09-15)"
      },
      "papers": [...],
      "paper_count": 20
    }
  }
}
```

## Technical Details

### 🔧 **Implementation**
- **Function**: `create_todays_knowledge_base()` in `app.py`
- **Helper Function**: `process_paper_for_kb()` for individual paper processing
- **Parallel Processing**: Uses ThreadPoolExecutor for efficient API calls
- **Error Handling**: Graceful handling of API failures and processing errors

### 📈 **Performance**
- Parallel fetching from all data sources
- Efficient paper processing with concurrent execution
- Progress tracking for user feedback
- Automatic directory creation

### 🛡️ **Error Handling**
- API failures are logged but don't stop the process
- Individual paper processing errors are handled gracefully
- Clear error messages for users
- Fallback behavior when no papers are found

## Use Cases

### 🎯 **Daily Research**
- Create a daily snapshot of the most relevant papers
- Build a collection of high-quality articles over time
- Track research trends on a daily basis

### 🔬 **RAG Integration**
- Use the structured JSON format for RAG systems
- Rich metadata for semantic search and filtering
- Consistent format with existing knowledge bases

### 📊 **Research Analysis**
- Analyze daily research patterns
- Compare relevance scores over time
- Track keyword trends and journal distributions

## Tips for Best Results

1. **Use Extended Mode**: For comprehensive results, select "Extended" search mode
2. **Enable All Sources**: Check all data sources for maximum coverage
3. **Refine Keywords**: Use specific, relevant keywords for better matching
4. **Regular Creation**: Create KB files regularly to build a comprehensive collection
5. **Monitor Progress**: Watch the progress bar for status updates

## Troubleshooting

### ❌ **No Papers Found**
- Check if today's date has any new publications
- Try enabling more data sources
- Verify your keywords are relevant to recent research

### ⚠️ **API Errors**
- Some sources may be temporarily unavailable
- The process continues with available sources
- Check the warning messages for specific issues

### 📁 **File Access Issues**
- Ensure you have write permissions in the app directory
- The `./KB/` directory is created automatically
- Check disk space if file creation fails

## Future Enhancements

- **Scheduled Creation**: Automatic daily KB creation
- **KB Management**: View, delete, and organize existing KB files
- **Export Options**: CSV export for KB files
- **KB Comparison**: Compare KB files across different dates
- **Integration**: Direct integration with RAG systems
