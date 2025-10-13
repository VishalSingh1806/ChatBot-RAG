# Contextual Suggestions Fix

## Problem Identified
The chatbot was showing the same generic suggestions regardless of user query context. Users asking about "EPR registration documents" were seeing the same suggestions as those asking about "penalties" or "recycling".

## Root Cause
The `generate_related_questions()` function in `search.py` was not being used effectively, and there was a problematic import from `faq_processor` that was causing issues.

## Solution Implemented

### 1. Enhanced Contextual Logic
Updated `generate_related_questions()` function to provide context-aware suggestions based on:

- **Registration queries** → Registration-related suggestions
- **Compliance queries** → Compliance-related suggestions  
- **Certificate queries** → Certificate-related suggestions
- **Penalty queries** → Penalty-related suggestions
- **Recycling queries** → Recycling-related suggestions
- **Producer queries** → Producer-specific suggestions
- **Importer queries** → Importer-specific suggestions
- **Brand owner queries** → Brand owner-specific suggestions
- **ReCircle queries** → ReCircle service suggestions

### 2. Fixed Import Issues
- Removed problematic `faq_processor` import from `search.py`
- Updated all ChromaDB path references to use centralized configuration
- Fixed path consistency across all files

### 3. Example Improvements

**Before (Generic):**
```
User: "What documents are needed for EPR registration?"
Suggestions: 
- What is EPR?
- What services does ReCircle offer?
- How do I register for EPR?
- What are EPR compliance requirements?
- How can I contact ReCircle?
```

**After (Contextual):**
```
User: "What documents are needed for EPR registration?"
Suggestions:
- What documents are needed for EPR registration?
- How long does EPR registration take?
- What is the EPR registration fee?
- How do I renew my EPR certificate?
- Can I register multiple brands under one EPR?
```

## Files Modified

1. **search.py** - Enhanced contextual suggestions logic
2. **config.py** - Centralized ChromaDB path configuration
3. **faq_processor.py** - Fixed ChromaDB path references
4. **test_suggestions.py** - New test script to verify functionality

## Testing

Run the test script to verify contextual suggestions:
```bash
python test_suggestions.py
```

## Expected Behavior

Now when users ask:
- **Registration questions** → Get registration-related suggestions
- **Compliance questions** → Get compliance-related suggestions
- **Penalty questions** → Get penalty-related suggestions
- **Recycling questions** → Get recycling-related suggestions
- **Company questions** → Get ReCircle service suggestions

The suggestions will be contextually relevant to their specific query domain, providing a much better user experience.