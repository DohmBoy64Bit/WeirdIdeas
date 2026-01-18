# Quality Gate Module

This module validates all generated moans before publishing or replying.

---

## 1. Inputs

- `comment_object`: Comment Object generated or adapted  
- `post_object`: Root Post Object  
- `subdeadit`: String, official subdeadit name  
- `persona`: Base Zombie Persona or override  
- `max_depth`: integer, usually 3  

---

## 2. Validation Steps

1. **Schema Validation**
   - All required fields exist: `comment_id`, `author`, `time_posted`, `body`, `upvotes`, `replies`, `parent_comment_id`  
   - Replies array ≤ max_depth  

2. **Persona Compliance**
   - Uses base zombie lexicon  
   - Tone matches persona: casual undead, mild dark humor  
   - Max 4 sentences per reply  

3. **Subdeadit Style Check**
   - Vocabulary matches allowed subdeadit lexicon  
   - Humor style correct  
   - Flair applied if subdeadit-specific  

4. **Parent Reference**
   - If parent_comment_id exists → body references parent author or moan  

5. **Safety Check**
   - No real-world locations or instructions  
   - No breaking immersion  

---

## 3. Output

- If valid → return comment_object  
- If invalid → return error object with reasons:

```
{
  "error": true,
  "reasons": [
    "Exceeded max depth",
    "Out-of-persona vocabulary",
    "Schema missing field: flair"
  ]
}
```

- Invalid comments are rejected and **never published**  

---

## 4. Modularity

- New validation rules can be added per subdeadit  
- Works with any new personas or archetypes without touching core generator  
- Ensures DRY and separation of concerns  

---

## 5. Example Flow

Input: Generated comment for r/BrainsGoneWild  

Check:

- Depth = 2 ✅  
- Vocabulary includes "buffet" ✅  
- Max 4 sentences ✅  
- Parent author referenced ✅  
- No real-world references ✅  

Result: **Passed** → publish to thread  
