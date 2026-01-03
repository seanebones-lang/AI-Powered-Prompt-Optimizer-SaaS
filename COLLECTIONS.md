# Grok Collections API Integration Guide

**Last Updated:** December 2025  
**Status:** Optional feature - RAG-enhanced prompt optimization

## Overview

The Grok Collections API (GA December 22, 2025) enables Retrieval-Augmented Generation (RAG) capabilities in our prompt optimizer. By uploading curated datasets of high-quality prompts, the Designer agent can semantically search through examples to create better optimized prompts.

## What is Grok Collections?

Grok Collections is xAI's integrated RAG solution that allows you to:
- Upload and store documents (PDFs, CSVs, Excel, text files, codebases)
- Perform semantic searches across documents
- Let Grok automatically search collections when relevant
- Reduce hallucinations and improve accuracy with domain-specific knowledge

### Key Features (December 2025)

- **Advanced Parsing**: OCR for scanned documents, layout-aware processing
- **Semantic Search**: Meaning-based retrieval using Grok's embedding models
- **Hybrid Search**: Combines semantic + keyword for best accuracy
- **Privacy**: User data isolated, not used for training
- **Benchmark Performance**: State-of-the-art in finance, legal, and coding domains

## Benefits for Prompt Optimizer

1. **Enhanced Quality**: Designer agent can reference high-quality prompt examples
2. **Domain-Specific**: Use collections for marketing, technical, or creative prompts
3. **Reduced Hallucinations**: Grounded in real examples rather than general knowledge
4. **Scalability**: Freemium users get basic optimization; paid users access larger collections

## Setup Instructions

### Step 1: Create Collections (via xAI Dashboard)

1. Visit [xAI Console](https://x.ai/console)
2. Navigate to Collections section
3. Create collections:
   - **General Prompt Examples**: Upload curated high-quality prompts
   - **Marketing Prompts** (optional): Marketing copy examples
   - **Technical Prompts** (optional): API docs, technical writing examples

### Step 2: Upload Documents

Upload files to your collections:
- **Supported formats**: PDF, CSV, Excel (.xlsx), TXT, code files
- **Recommendations**:
  - Start with 10-20 high-quality prompt examples
  - Include diverse examples (different styles, domains)
  - Add metadata/tags if possible

### Step 3: Configure Environment

Edit your `.env` file:

```env
# Enable Collections (set to true when ready)
ENABLE_COLLECTIONS=true

# Collection IDs from xAI dashboard
COLLECTION_ID_PROMPT_EXAMPLES=col_abc123xyz
COLLECTION_ID_MARKETING=col_marketing456
COLLECTION_ID_TECHNICAL=col_tech789
```

### Step 4: Restart Application

```bash
streamlit run main.py
```

## How It Works

When Collections is enabled:

1. **Designer Agent Enhancement**: The Designer agent automatically receives access to the `file_search` tool
2. **Autonomous Searching**: Grok decides when to search collections based on the prompt type and optimization needs
3. **Semantic Matching**: Finds relevant prompt examples using semantic search
4. **Enhanced Output**: Designer incorporates examples into optimized prompt design

### Example Flow

```
User Prompt: "Write a blog post about AI"
    ↓
Deconstructor → Diagnoser → Designer (with Collections)
    ↓
Designer searches: "blog post writing prompts", "AI content prompts"
    ↓
Grok retrieves relevant examples from collections
    ↓
Designer creates optimized prompt inspired by examples
    ↓
Enhanced optimized prompt with domain-specific best practices
```

## Configuration

### Enable/Disable Collections

In `config.py` or `.env`:

```python
enable_collections: bool = True  # Set to False to disable
```

### Collection IDs by Prompt Type

The system automatically selects appropriate collections:

- **General**: Uses `COLLECTION_ID_PROMPT_EXAMPLES` for all types
- **Marketing/Creative**: Also uses `COLLECTION_ID_MARKETING`
- **Technical/Analytical**: Also uses `COLLECTION_ID_TECHNICAL`

### Search Parameters

Collections search uses:
- **Search Type**: Hybrid (semantic + keyword) by default
- **Limit**: 5 results (configurable 1-10)
- **Automatic**: Grok decides when to search

## Best Practices

### Collection Management

1. **Start Small**: Begin with 10-20 high-quality examples
2. **Curate Quality**: Focus on excellent prompts, not quantity
3. **Organize by Type**: Separate collections for different domains
4. **Regular Updates**: Add new examples as you discover them
5. **Test Results**: Verify Collections improves optimization quality

### Prompt Dataset Preparation

**Good Examples:**
- Clear, well-structured prompts
- Diverse styles and formats
- Domain-specific expertise
- Proven effective prompts

**Avoid:**
- Low-quality or ambiguous prompts
- Duplicates
- Overly specific examples (limit generalizability)

### Cost Considerations

- **Indexing**: Free (one-time per upload)
- **Searches**: Count toward token usage ($0.15/1M tokens for Grok 4.1 Fast)
- **Monitoring**: Track usage via xAI dashboard

## Testing

### Verify Collections is Working

1. Enable Collections in `.env`
2. Run optimization for a prompt
3. Check logs for "Collections search requested" messages
4. Review optimized prompts - they should reference or be inspired by examples

### Test Queries

Try prompts that should benefit from examples:
- Marketing: "Write a product launch email"
- Technical: "Explain API authentication"
- Creative: "Write a short story opening"

## Troubleshooting

### Collections Not Working

**Issue**: Designer agent doesn't search collections

**Solutions**:
- Verify `ENABLE_COLLECTIONS=true` in `.env`
- Check collection IDs are correct
- Ensure collections have documents uploaded
- Check API key has Collections access

### No Results Found

**Issue**: Searches return no results

**Solutions**:
- Verify documents are uploaded and indexed
- Check collection IDs match dashboard
- Try broader search queries
- Verify file formats are supported

### Performance Issues

**Issue**: Slow optimization times

**Solutions**:
- Reduce search limit (default: 5)
- Use smaller collections
- Consider caching search results
- Monitor API response times

## API Details

### Tool Definition

Collections uses the `file_search` tool (OpenAI-compatible):

```python
{
    "type": "function",
    "function": {
        "name": "file_search",
        "description": "Search through uploaded document collections...",
        "parameters": {
            "query": "search query",
            "collection_ids": ["col_123"],
            "limit": 5,
            "search_type": "hybrid"
        }
    }
}
```

### Direct API Access

For advanced use cases, you can use xAI's Collections API directly:

```python
# Collection management
POST /collections
GET /collections/{id}
DELETE /collections/{id}

# File management
POST /collections/{id}/files
GET /collections/{id}/files

# Search
POST /collections/{id}/search
```

See [xAI API Documentation](https://x.ai/api) for details.

## Roadmap Integration

### Phase 2 (MVP Development)
- [x] Collections API integration code
- [x] Configuration system
- [ ] Initial collection creation (curate examples)
- [ ] Testing with sample datasets

### Phase 3 (Testing & Iteration)
- [ ] Validate Collections improves optimization quality
- [ ] Performance testing
- [ ] Cost analysis
- [ ] User feedback on RAG-enhanced outputs

### Phase 5 (Post-Launch)
- [ ] Premium feature: Larger collections
- [ ] User-uploaded collections (paid tier)
- [ ] Collection marketplace/templates
- [ ] Multi-collection searches

## References

- [xAI Collections Documentation](https://x.ai/api/collections)
- [xAI Console](https://x.ai/console)
- [RAG Best Practices](https://x.ai/blog/collections-api)
- Project Roadmap: See `ROADMAP.md`

## Support

For issues or questions:
- Check xAI API documentation
- Review logs for error messages
- Verify collection configuration
- Test with minimal setup first

---

**Note**: Collections is an optional feature. The app works perfectly without it, but RAG enhances optimization quality when enabled.
