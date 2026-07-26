
## 2024-07-18 - String Checking Bottlenecks
**Learning:** Checking for multiple substrings in a python string using `any(k in string.lower() for k in keywords)` is significantly slower than using a pre-compiled `re.compile(r'word1|word2|word3', re.IGNORECASE).search(string)`, especially on critical data paths like text classification routing (`siniflandir` in `otonom.py`). Avoiding the `.lower()` string allocation per execution also speeds up the operation.
**Action:** Use `re.compile` with `re.IGNORECASE` for matching multiple keywords instead of list comprehensions with `in`.
## 2025-01-26 - [Optimize string matching]
**Learning:** For Python performance optimizations involving string matching in hot paths, prefer iterating through globally scoped immutable tuples using C-level 'in' checks over regex '.findall()' or locally allocated lists to avoid object recreation overhead.
**Action:** Applied this optimization in `agentik_dongu.py` by converting locally allocated keyword lists in `gorev_tipini_belirle` and `AgentSBridge.calistir` to globally scoped immutable tuples.
