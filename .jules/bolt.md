
## 2024-07-18 - String Checking Bottlenecks
**Learning:** Checking for multiple substrings in a python string using `any(k in string.lower() for k in keywords)` is significantly slower than using a pre-compiled `re.compile(r'word1|word2|word3', re.IGNORECASE).search(string)`, especially on critical data paths like text classification routing (`siniflandir` in `otonom.py`). Avoiding the `.lower()` string allocation per execution also speeds up the operation.
**Action:** Use `re.compile` with `re.IGNORECASE` for matching multiple keywords instead of list comprehensions with `in`.

## 2026-08-03 - [Routing String Allocation Optimization]
**Learning:** In hot paths (e.g., text classification routing), using list comprehensions with `in` operators for string matching introduces unnecessary per-execution string allocation overhead.
**Action:** Replaced static `sum(1 for kw in keywords if kw in g)` list comprehensions with pre-compiled module-level Regex objects (`re.compile(..., re.IGNORECASE).search(string)`), optimizing execution time and CPU overhead.
