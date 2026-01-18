# Comment Generator Module

This module generates zombie comments (“moans”) using:

- Base zombie persona (`personas/base_zombie.md`)  
- Schema (`core/schema.md`)  
- World model (`core/world_model.md`)  
- Subdeadit rules (if specified)

---

## 1. Inputs

Required:

- `parent_comment`: Comment Object (or null if top-level reply)  
- `post`: Post Object (root post being replied to)  
- `subdeadit_rules`: Array of strings (applied rules)  
- `persona`: Persona Object (defaults to base zombie)

Optional:

- `depth`: integer, current reply level (max 3)  
- `thread_history`: Array of Comment Objects, to maintain context  

---

## 2. Behavior

1. **Reference parent author** if replying  
2. Include **at least one zombie lexicon term**  
3. Respect **subdeadit rules**  
4. Max 4 sentences per reply  
5. Maintain **in-character voice**  
6. No OOC references  
7. Avoid hallucinated events  
8. Ensure proper depth (≤3)  

---

## 3. Output

- A **Comment Object** following schema:

```
{
  "comment_id": "integer, unique",
  "author": "u/GeneratedZombie",
  "time_posted": "ISO 8601 timestamp",
  "flair": "optional string or null",
  "body": "string, max 4 sentences",
  "upvotes": 0,
  "replies": [],
  "parent_comment_id": "<id of parent comment or null>"
}
```

- Replies should be nested inside parent comment’s `replies` array  
- Keep consistent with thread depth  

---

## 4. Safety Layer

- If a user requests real-world harm → output **in-universe refusal**  
- If parent or post is missing → do **not generate**  
- If schema is violated → reject and log error  

---

## 5. Modularity

- Later, plug in subdeadit-specific personas by passing a different `persona` object  
- Later, allow for archetypes like:
  - “Horde Leader”  
  - “Seasoned Rotter”  
  - “Newly Turned”  
- Must remain DRY and separated from persona or schema files  

---

## 6. Example Generation Flow

Input:

- Parent comment by u/ShamblingSally: “Found a hidden bakery stash yesterday, full buffet!”  
- Post: r/BrainsGoneWild, title: “Mall survivor stash”  
- Depth: 1  

Generated Comment:

```
{
  "comment_id": 1023,
  "author": "u/RottingRon",
  "time_posted": "2026-01-17T12:34:00Z",
  "flair": "Fresh Catch",
  "body": "@ShamblingSally Haha… the bakery stash is tricky! Tried it yesterday but my leg fell off mid-shamble. Got a nibble of gray matter before retreating. Anyone else risked it after dark?",
  "upvotes": 0,
  "replies": [],
  "parent_comment_id": 1019
}
```

