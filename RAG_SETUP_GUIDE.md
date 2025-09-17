# 🧠 RAG System Setup Guide

This guide will help you set up the RAG (Retrieval-Augmented Generation) system for the Manuscript Alert application.

## 📋 Overview

The RAG system allows you to:
- Ask questions about recent research papers
- Get AI-powered insights and summaries
- Find relevant papers based on natural language queries
- Generate weekly research summaries

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install RAG-specific dependencies
pip install -r requirements_rag.txt

# Or install individual packages
pip install sentence-transformers transformers torch numpy scikit-learn requests
```

### 2. Choose Your LLM Option

The RAG system supports multiple free LLM options:

#### Option A: Hugging Face (Recommended for beginners)
- **Pros**: Free, no setup required, good for testing
- **Cons**: Rate limited, slower responses
- **Setup**: No additional setup needed

#### Option B: Groq (Recommended for best performance)
- **Pros**: Very fast, free tier available, high-quality models
- **Cons**: Requires API key
- **Setup**:
  ```bash
  # Get free API key from https://console.groq.com/
  export GROQ_API_KEY="your_api_key_here"
  ```

#### Option C: Ollama (Recommended for local use)
- **Pros**: Completely local, no API limits, privacy-focused
- **Cons**: Requires local setup, needs good hardware
- **Setup**:
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.ai/install.sh | sh
  
  # Pull a model (this will take a while)
  ollama pull llama2:7b
  
  # Start Ollama server
  ollama serve
  ```

#### Option D: Local Transformers
- **Pros**: No external dependencies, works offline
- **Cons**: Requires significant RAM, slower
- **Setup**: No additional setup needed (but requires 4GB+ RAM)

### 3. Initialize the RAG System

1. Start the app: `streamlit run app.py`
2. Go to the "🧠 RAG Assistant" tab
3. Configure your LLM settings in the "⚙️ RAG Configuration" section
4. Click "🚀 Initialize RAG System"

## 🔧 Configuration Options

### LLM Client Types

| Client | Model Examples | Best For |
|--------|----------------|----------|
| **Hugging Face** | `microsoft/DialoGPT-medium`, `gpt2` | Testing, quick setup |
| **Groq** | `llama2-7b-4096`, `mixtral-8x7b-32768` | Production use, speed |
| **Ollama** | `llama2:7b`, `llama2:13b` | Local use, privacy |
| **Local** | `microsoft/DialoGPT-small`, `gpt2` | Offline use |

### Advanced Settings

- **Documents to retrieve**: Number of papers to use as context (3-15)
- **Force rebuild index**: Rebuild the vector store from scratch
- **Metadata filtering**: Filter by source, journal, date range

## 📚 Usage Examples

### Basic Queries

```
"What are the latest findings on amyloid PET imaging?"
"What's new in deep-learning based tau prediction this week?"
"What are the most significant research developments in Alzheimer's disease this week?"
```

### Advanced Queries

```
"Compare the effectiveness of different MRI sequences for detecting early Alzheimer's"
"What are the emerging biomarkers for dementia diagnosis?"
"How has machine learning improved neuroimaging analysis in the past month?"
```

### Weekly Summaries

The system can generate comprehensive weekly summaries that include:
- Key research themes
- Notable findings
- Methodological advances
- Clinical implications
- Future research directions

## 🛠️ Troubleshooting

### Common Issues

#### 1. "RAG system not available"
- **Cause**: Missing dependencies
- **Solution**: Install requirements: `pip install -r requirements_rag.txt`

#### 2. "LLM client not available"
- **Cause**: Service not running or API key missing
- **Solution**: 
  - For Ollama: Start server with `ollama serve`
  - For Groq: Set `GROQ_API_KEY` environment variable
  - For Hugging Face: Check internet connection

#### 3. "No papers found in knowledge base"
- **Cause**: No KB files in `./KB/` directory
- **Solution**: Create knowledge base using the "📚 Create Today's KB" button

#### 4. Slow responses
- **Cause**: Large models or slow internet
- **Solution**: 
  - Use smaller models (e.g., `gpt2` instead of `llama2:7b`)
  - Reduce "Documents to retrieve" setting
  - Use Groq for faster responses

#### 5. Memory issues
- **Cause**: Large models loading into memory
- **Solution**:
  - Use Hugging Face or Groq instead of local models
  - Reduce chunk size in text processing
  - Close other applications

### Performance Optimization

1. **Use Groq for best performance**: Fastest responses with good quality
2. **Adjust document retrieval**: Start with 5 documents, increase if needed
3. **Cache vector store**: The system caches embeddings to avoid recomputation
4. **Filter by metadata**: Use source/journal filters to reduce search space

## 🔍 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Knowledge     │    │   Text           │    │   Vector        │
│   Base Loader   │───▶│   Processor      │───▶│   Store         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│   LLM Client    │◀───│   RAG System     │◀────────────┘
└─────────────────┘    └──────────────────┘
```

### Components

1. **Knowledge Base Loader**: Loads and processes KB files
2. **Text Processor**: Chunks and preprocesses text
3. **Vector Store**: Creates embeddings and handles similarity search
4. **LLM Client**: Generates responses using various LLM services
5. **RAG System**: Coordinates all components

## 📊 Monitoring and Maintenance

### System Status

Check the "📊 System Status" section to monitor:
- Total papers in knowledge base
- Vector store document count
- LLM client availability
- Source distribution

### Regular Maintenance

1. **Update knowledge base**: Use "📚 Create Today's KB" regularly
2. **Rebuild index**: Use "Force rebuild index" if you notice issues
3. **Monitor performance**: Check response times and quality
4. **Update models**: Keep LLM models updated for best results

## 🎯 Best Practices

### Query Formulation

- **Be specific**: "What are the latest findings on tau PET imaging in early Alzheimer's?" vs "What's new?"
- **Use domain terms**: Include technical terms like "amyloid", "PET", "MRI"
- **Ask focused questions**: Break complex queries into smaller parts

### System Usage

- **Start simple**: Begin with basic queries to test the system
- **Use quick actions**: Try the preset buttons for common questions
- **Filter results**: Use metadata filtering for more targeted results
- **Generate summaries**: Use weekly summaries for comprehensive overviews

### Performance Tips

- **Choose appropriate LLM**: Match model size to your hardware
- **Optimize retrieval**: Adjust document count based on query complexity
- **Cache effectively**: Let the system cache embeddings for faster subsequent queries
- **Monitor resources**: Watch memory and CPU usage with local models

## 🔮 Future Enhancements

Planned features:
- Multi-modal support (images, figures)
- Citation tracking and verification
- Collaborative filtering
- Advanced analytics and trends
- Integration with reference managers
- Export to various formats

## 📞 Support

If you encounter issues:
1. Check this guide for common solutions
2. Verify all dependencies are installed
3. Check system status in the app
4. Try different LLM clients
5. Rebuild the vector store index

For advanced issues, check the logs in the Streamlit interface or examine the cache directory (`./rag_cache/`).
