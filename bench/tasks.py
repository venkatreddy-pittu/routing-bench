"""Self-written code-repair tasks. Each has a buggy file, pytest tests, and a reference fix.

STARTER SET: 9 tasks (3 per tier). Grow to 45 (15 per tier) BEFORE running any model, then freeze.
Tier 1 = single function, one bug. Tier 2 = edge-case logic. Tier 3 = stateful class, multiple interacting bugs.
Write your own tasks; do not copy public benchmarks (models may have seen them).
"""

TASKS = [
    # ---------------- Tier 1 ----------------
    dict(
        id="t1_moving_average", tier=1,
        spec="moving_average(values, window) returns the list of averages of every consecutive window of the given size. If window > len(values) return [].",
        buggy="""def moving_average(values, window):
    out = []
    for i in range(len(values) - window):
        out.append(sum(values[i:i + window]) / window)
    return out
""",
        ref="""def moving_average(values, window):
    out = []
    for i in range(len(values) - window + 1):
        out.append(sum(values[i:i + window]) / window)
    return out
""",
        tests="""from solution import moving_average

def test_basic():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]

def test_full_window():
    assert moving_average([2, 4, 6], 3) == [4.0]

def test_window_too_big():
    assert moving_average([1, 2], 5) == []
""",
    ),
    dict(
        id="t1_palindrome", tier=1,
        spec="is_palindrome(s) is True if s reads the same forwards and backwards, ignoring case and any non-alphanumeric characters. The empty string is a palindrome.",
        buggy="""def is_palindrome(s):
    cleaned = [c for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
""",
        ref="""def is_palindrome(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
""",
        tests="""from solution import is_palindrome

def test_sentence():
    assert is_palindrome("A man, a plan, a canal: Panama")

def test_not():
    assert not is_palindrome("hello")

def test_empty_and_case():
    assert is_palindrome("")
    assert is_palindrome("Aa")
""",
    ),
    dict(
        id="t1_chunk", tier=1,
        spec="chunk(lst, n) splits lst into consecutive sublists of length n (n >= 1). The last chunk may be shorter. chunk([]) returns [].",
        buggy="""def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst) - len(lst) % n, n)]
""",
        ref="""def chunk(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]
""",
        tests="""from solution import chunk

def test_remainder():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

def test_empty():
    assert chunk([], 3) == []

def test_short_list():
    assert chunk([1, 2], 5) == [[1, 2]]
""",
    ),
    # ---------------- Tier 2 ----------------
    dict(
        id="t2_merge_intervals", tier=2,
        spec="merge_intervals(intervals) takes a list of [start, end] pairs in any order and returns merged, sorted, non-overlapping intervals. Intervals that touch (end == next start) are merged. Nested intervals keep the larger end.",
        buggy="""def merge_intervals(intervals):
    merged = []
    for start, end in intervals:
        if merged and start < merged[-1][1]:
            merged[-1][1] = end
        else:
            merged.append([start, end])
    return merged
""",
        ref="""def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""",
        tests="""from solution import merge_intervals

def test_unsorted():
    assert merge_intervals([[5, 6], [1, 3], [2, 4]]) == [[1, 4], [5, 6]]

def test_touching():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]

def test_nested():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]

def test_empty():
    assert merge_intervals([]) == []
""",
    ),
    dict(
        id="t2_parse_duration", tier=2,
        spec="parse_duration(s) converts strings like '1h30m', '90s', '2h', '100m', '1h1m1s' to total seconds. Units are h, m, s; any subset may appear; numbers can have multiple digits. Empty string returns 0.",
        buggy="""def parse_duration(s):
    total = 0
    num = 0
    for ch in s:
        if ch.isdigit():
            num = int(ch)
        elif ch == "h":
            total += num * 3600
        elif ch == "m":
            total += num * 60
        elif ch == "s":
            total += num
    return total
""",
        ref="""def parse_duration(s):
    units = {"h": 3600, "m": 60, "s": 1}
    total = 0
    num = 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch in units:
            total += num * units[ch]
            num = 0
    return total
""",
        tests="""from solution import parse_duration

def test_multi_digit():
    assert parse_duration("90s") == 90
    assert parse_duration("100m") == 6000

def test_combined():
    assert parse_duration("1h30m") == 5400
    assert parse_duration("1h1m1s") == 3661

def test_single_and_empty():
    assert parse_duration("2h") == 7200
    assert parse_duration("") == 0
""",
    ),
    dict(
        id="t2_top_k", tier=2,
        spec="top_k_frequent(words, k) returns the k most frequent words, most frequent first. Ties are broken alphabetically. If k exceeds the number of distinct words, return all of them.",
        buggy="""from collections import Counter

def top_k_frequent(words, k):
    return [w for w, _ in Counter(words).most_common(k)]
""",
        ref="""from collections import Counter

def top_k_frequent(words, k):
    counts = Counter(words)
    return sorted(counts, key=lambda w: (-counts[w], w))[:k]
""",
        tests="""from solution import top_k_frequent

def test_tie_break():
    assert top_k_frequent(["b", "a", "b", "a", "c"], 2) == ["a", "b"]

def test_order():
    assert top_k_frequent(["x", "y", "y", "z", "z", "z"], 3) == ["z", "y", "x"]

def test_k_too_large():
    assert top_k_frequent(["a", "b"], 5) == ["a", "b"]
""",
    ),
    # ---------------- Tier 3 ----------------
    dict(
        id="t3_lru_cache", tier=3,
        spec="LRUCache(capacity): get(key) returns the value or -1 and marks the key most recently used. put(key, value) inserts or updates, marks the key most recently used, and evicts the least recently used key when over capacity.",
        buggy="""class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}

    def get(self, key):
        return self.data.get(key, -1)

    def put(self, key, value):
        if key not in self.data and len(self.data) >= self.capacity:
            oldest = next(iter(self.data))
            del self.data[oldest]
        self.data[key] = value
""",
        ref="""class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}

    def get(self, key):
        if key not in self.data:
            return -1
        value = self.data.pop(key)
        self.data[key] = value
        return value

    def put(self, key, value):
        if key in self.data:
            self.data.pop(key)
        elif len(self.data) >= self.capacity:
            del self.data[next(iter(self.data))]
        self.data[key] = value
""",
        tests="""from solution import LRUCache

def test_get_refreshes():
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    assert c.get(1) == 1
    assert c.get(3) == 3

def test_update_refreshes():
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2); c.put(1, 10); c.put(3, 3)
    assert c.get(2) == -1
    assert c.get(1) == 10

def test_capacity_one():
    c = LRUCache(1)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == -1
    assert c.get(2) == 2
""",
    ),
    dict(
        id="t3_rate_limiter", tier=3,
        spec="RateLimiter(max_calls, period): allow(now) returns True and records the call if fewer than max_calls ALLOWED calls were made in the last `period` seconds (a call at time t counts for times in [t, t + period)). Denied calls are not recorded. now is non-decreasing.",
        buggy="""class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def allow(self, now):
        self.calls.append(now)
        recent = [t for t in self.calls if now - t <= self.period]
        return len(recent) <= self.max_calls
""",
        ref="""class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def allow(self, now):
        self.calls = [t for t in self.calls if now - t < self.period]
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
""",
        tests="""from solution import RateLimiter

def test_limit():
    r = RateLimiter(2, 10)
    assert r.allow(0)
    assert r.allow(1)
    assert not r.allow(2)

def test_window_boundary():
    r = RateLimiter(2, 10)
    r.allow(0); r.allow(1); r.allow(2)
    assert r.allow(10)
    assert not r.allow(10.5)

def test_denied_not_recorded():
    r = RateLimiter(2, 10)
    r.allow(0); r.allow(1)
    assert not r.allow(2)
    r.allow(10)
    assert r.allow(11)
""",
    ),
    dict(
        id="t3_inventory", tier=3,
        spec="Inventory: add(item, qty) adds to the existing quantity. remove(item, qty) subtracts; unknown item raises KeyError; removing more than available raises ValueError and leaves stock unchanged. Items that reach 0 are dropped. report() returns a sorted list of (item, qty) tuples.",
        buggy="""class Inventory:
    def __init__(self):
        self.stock = {}

    def add(self, item, qty):
        self.stock[item] = qty

    def remove(self, item, qty):
        self.stock[item] -= qty
        if self.stock[item] < 0:
            raise ValueError("insufficient stock")

    def report(self):
        return sorted(self.stock.items())
""",
        ref="""class Inventory:
    def __init__(self):
        self.stock = {}

    def add(self, item, qty):
        self.stock[item] = self.stock.get(item, 0) + qty

    def remove(self, item, qty):
        if item not in self.stock:
            raise KeyError(item)
        if self.stock[item] < qty:
            raise ValueError("insufficient stock")
        self.stock[item] -= qty
        if self.stock[item] == 0:
            del self.stock[item]

    def report(self):
        return sorted(self.stock.items())
""",
        tests="""import pytest
from solution import Inventory

def test_add_accumulates():
    inv = Inventory()
    inv.add("a", 2); inv.add("a", 3)
    assert inv.report() == [("a", 5)]

def test_zero_dropped():
    inv = Inventory()
    inv.add("a", 2); inv.remove("a", 2)
    assert inv.report() == []

def test_failed_remove_keeps_state():
    inv = Inventory()
    inv.add("a", 2)
    with pytest.raises(ValueError):
        inv.remove("a", 5)
    assert inv.report() == [("a", 2)]

def test_unknown_item():
    with pytest.raises(KeyError):
        Inventory().remove("zzz", 1)
""",
    ),
]
