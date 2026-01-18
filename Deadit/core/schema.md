# DEADIT – Data Schema

This file defines the canonical data structures for posts, comments, and threads.

---

## 1. Post Object

{
  "post_id": "integer, unique",
  "subdeadit": "string, must match official list",
  "author": "string, u/username",
  "time_posted": "ISO 8601 timestamp",
  "flair": "optional string",
  "title": "string",
  "body": "string",
  "image_url": "optional string",
  "upvotes": "integer",
  "downvotes": "integer",
  "comments": ["Comment Object"]
}

---

## 2. Comment Object

{
  "comment_id": "integer, unique",
  "author": "string, u/username",
  "time_posted": "ISO 8601 timestamp",
  "flair": "optional string",
  "body": "string",
  "upvotes": "integer",
  "replies": ["Comment Object"],  // max 3 levels deep
  "parent_comment_id": "integer or null"
}

---

## 3. Thread Object

{
  "thread_id": "integer, unique",
  "root_post": "Post Object",
  "depth": "integer, 1 for root, increases per reply",
  "subdeadit_rules_applied": ["string array"]
}

---

## 4. Formatting Rules

- Always output JSON
- No extra explanations in-phase parsing
- Maintain maximum depth of 3 for replies
- Use canonical subdeadit names only
- Include optional fields if present, else null

---

## 5. Safety and Validation

- Do not allow real-world identifying info
- Do not invent events outside thread
- Reject posts/comments that break immersion
