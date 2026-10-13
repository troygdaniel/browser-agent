---
name: Model Performance Report
about: Report how well a specific Ollama model works
title: '[MODEL] Model Name Performance'
labels: model-testing
---

## Model Information
- **Model Name:** <!-- e.g., qwen2.5:14b -->
- **Parameter Count:** <!-- e.g., 14B -->
- **Model Type:** <!-- e.g., general, code, chat -->

## Test Results

### Simple Tasks
<!-- Rate: ⭐⭐⭐⭐⭐ -->
**Rating:**

**Example Task:**
```bash
browser-agent run "Go to example.com"
```

**Result:**
- ✅ / ❌ Completed successfully
- Steps taken:
- Issues encountered:

### Complex Tasks
<!-- Rate: ⭐⭐⭐⭐⭐ -->
**Rating:**

**Example Task:**
```bash
browser-agent run "Navigate to Python.org, search for 'asyncio', and summarize the first result"
```

**Result:**
- ✅ / ❌ Completed successfully
- Steps taken:
- Issues encountered:

## Overall Assessment
<!-- Summary of model performance -->

## Recommended Use Cases
<!-- What this model is good/bad for -->

## Configuration Used
<!-- Paste your configs/home.yaml settings -->

```yaml
ollama:
  model: your-model-here
  # other settings
```
