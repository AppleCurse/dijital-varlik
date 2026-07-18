
## 2024-07-18 - String Checking Bottlenecks
**Learning:** Checking for multiple substrings in a python string using `any(k in string.lower() for k in keywords)` is significantly slower than using a pre-compiled `re.compile(r'word1|word2|word3', re.IGNORECASE).search(string)`, especially on critical data paths like text classification routing (`siniflandir` in `otonom.py`). Avoiding the `.lower()` string allocation per execution also speeds up the operation.
**Action:** Use `re.compile` with `re.IGNORECASE` for matching multiple keywords instead of list comprehensions with `in`.
