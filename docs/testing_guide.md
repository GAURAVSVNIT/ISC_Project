
# Testing Guide: Multimodal Verification Model

This guide outlines how to test the Project Veritas Phase 2 Reasoning Core using Images + Text Captions.

## Prerequisites
- Python 3.9+
- OpenAI API Key (GPT-4o access)
- SerpApi Key

## Environment Setup
Ensure your `.env` file is configured:
```env
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...
```

## Testing Scripts

### 1. Test Context Grounding (Stream C)
Verifies that the system can fetch and filter web context for a given claim.
```bash
python backend/test_connection.py
```

### 2. Test Full Reasoning Pipeline (Image + Text)
We have provided a dedicated test script `backend/test_pipeline.py` which invokes the **Orchestrator** to run all streams in parallel.

**Usage:**
```bash
python backend/test_pipeline.py --image "path/to/image.jpg" --caption "Your claim here"
```

If no arguments are provided, it defaults to a sample URL and claim.

## Manual Testing Steps

1. **Identify a Test Case**: Find an image (real or fake) and a specific claim about it.
2. **Run the Pipeline**:
   - The **Orchestrator** initializes 3 streams (Visual, Semantic, Context).
   - It runs them in parallel using `asyncio.gather`.
   - It aggregates evidence and uses `LLMReasoner` to build the prompt.
   - It executes the final verdict call to GPT-4o.
3. **Analyze Output**:
   - Check `verdict`: Should be FAKE or MISLEADING.
   - Check `stream_data`: Verify that Context Stream returned results and others (Visual/Semantic) returned their placeholder status.
   - Check `explanation`: Should be a clear, user-facing paragraph.

## Trouble Shooting
- **"Image processing failed"**: Ensure local paths are absolute. URLs must be publicly accessible.
- **"Context not found"**: Try a more specific caption/query.
- **"API Key missing"**: Check `.env` and ensure keys are loaded.
