
## 2024-07-18 - String Checking Bottlenecks
**Learning:** Checking for multiple substrings in a python string using `any(k in string.lower() for k in keywords)` is significantly slower than using a pre-compiled `re.compile(r'word1|word2|word3', re.IGNORECASE).search(string)`, especially on critical data paths like text classification routing (`siniflandir` in `otonom.py`). Avoiding the `.lower()` string allocation per execution also speeds up the operation.
**Action:** Use `re.compile` with `re.IGNORECASE` for matching multiple keywords instead of list comprehensions with `in`.
## 2024-07-25 - Keyword Matching Performance in Python
**Learning:** In hot paths (like `gorev_tipini_belirle`), using `sum()` with a generator expression inside (e.g., `sum(1 for kw in keywords if kw in target)`) introduces significant overhead compared to explicitly maintaining a count and incrementing it within a `for` loop. Additionally, allocating local lists for keywords inside the function creates recreation overhead every time the function is called.
**Action:** Extract immutable reference data (like keyword arrays) to globally scoped tuples and favor standard `for` loops with a counter variable instead of `sum()` generator expressions when performance is critical.
