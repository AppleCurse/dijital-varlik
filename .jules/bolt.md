## 2026-07-20 - [Avoid local list allocation for string matching]
**Learning:** Instantiating lists (like `["word1", "word2"]`) inside frequently called functions causes unnecessary object recreation overhead.
**Action:** Always use globally scoped immutable tuples (e.g. `WEB_KEYWORDS = ("word1", "word2")`) for keyword matching in hot paths to minimize object allocation overhead.