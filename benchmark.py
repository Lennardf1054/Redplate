"""Timing tests for the algorithm comparison.
Run from the Redplate folder:  python benchmark.py
"""
import csv
import os
import random
import time

import config
from Back_End.algorithm import binary_search, bubble_sort, linear_search, merge_sort
from Back_End.Structures.bst import BST

SIZES = [100, 1000, 10000]
SEARCHES = 1000                          # lookups per timing run
REPEATS = {100: 5, 1000: 3, 10000: 1}    # runs per size; we keep the fastest
results = []                             # rows for the CSV file


def make_orders(n):
    """Fake orders numbered 1..n (so already sorted by order_no) with random totals."""
    return [{"order_no": i, "total": random.randint(20, 500)} for i in range(1, n + 1)]


def build_bst(orders):
    tree = BST()
    for order in orders:
        tree.insert(order["order_no"], order)
    return tree


def best_time(func, repeats):
    """Run func several times and return (fastest time in seconds, last result)."""
    best = None
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        if best is None or elapsed < best:
            best = elapsed
    return best, result


def run_searches(search_one, targets):
    for target in targets:
        search_one(target)


def benchmark_search(datasets, trees):
    for scenario in ("random targets", "worst case (last order)"):
        print(f"\nSEARCH: {SEARCHES} lookups by order number, {scenario}")
        print(f"{'orders':>8} {'linear ms':>11} {'binary ms':>11} {'BST ms':>11}")
        for n in SIZES:
            orders = datasets[n]
            tree = trees[n]
            if scenario == "random targets":
                targets = [random.randint(1, n) for _ in range(SEARCHES)]
            else:
                targets = [n] * SEARCHES

            for t in targets[:50]:                       # all three must find the same order
                assert orders[linear_search(orders, t)]["order_no"] == t
                assert orders[binary_search(orders, t)]["order_no"] == t
                assert tree.search(t)["order_no"] == t

            contenders = {
                "linear": lambda t: linear_search(orders, t),
                "binary": lambda t: binary_search(orders, t),
                "bst": lambda t: tree.search(t),
            }
            times = {}
            for name, search_one in contenders.items():
                times[name], _ = best_time(lambda: run_searches(search_one, targets), REPEATS[n])
                results.append(["search", scenario, name, n, times[name]])

            print(f"{n:>8,} {times['linear'] * 1000:>11.3f} "
                  f"{times['binary'] * 1000:>11.3f} {times['bst'] * 1000:>11.3f}")


def benchmark_sort(datasets):
    print("\nSORT: orders by total (random data)")
    print(f"{'orders':>8} {'bubble ms':>11} {'merge ms':>11} {'merge is faster by':>20}")
    for n in SIZES:
        data = datasets[n]
        if n == 10000:
            print("  (bubble sort on 10,000 orders can take a minute...)", flush=True)
        bubble, bubble_result = best_time(lambda: bubble_sort(data, "total"), REPEATS[n])
        merge, merge_result = best_time(lambda: merge_sort(data, "total"), REPEATS[n])
        assert bubble_result == merge_result             # both must give the same answer
        results.append(["sort", "random", "bubble", n, bubble])
        results.append(["sort", "random", "merge", n, merge])
        print(f"{n:>8,} {bubble * 1000:>11.3f} {merge * 1000:>11.3f} {bubble / merge:>19.1f}x")


def benchmark_sort_cases(datasets):
    n = 1000
    base = datasets[n]
    ascending = sorted(base, key=lambda o: o["total"])   # built-in sorted() only prepares test data
    cases = {"random": base, "already sorted": ascending, "reversed": ascending[::-1]}
    print(f"\nSORT: {n:,} orders, different starting orders")
    print(f"{'case':>16} {'bubble ms':>11} {'merge ms':>11}")
    for name, data in cases.items():
        bubble, bubble_result = best_time(lambda: bubble_sort(data, "total"), REPEATS[n])
        merge, merge_result = best_time(lambda: merge_sort(data, "total"), REPEATS[n])
        assert bubble_result == merge_result
        results.append(["sort", name, "bubble", n, bubble])
        results.append(["sort", name, "merge", n, merge])
        print(f"{name:>16} {bubble * 1000:>11.3f} {merge * 1000:>11.3f}")


def save_csv():
    path = os.path.join(config.BASE_DIR, "benchmark_results.csv")
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["problem", "scenario", "algorithm", "size", "seconds"])
        writer.writerows(results)
    print(f"\nSaved all results to {path}")


if __name__ == "__main__":
    random.seed(411)                                     # same fake data every run
    datasets = {n: make_orders(n) for n in SIZES}
    trees = {}
    for n in SIZES:
        print(f"Building a BST with {n:,} orders...", flush=True)
        trees[n] = build_bst(datasets[n])
    benchmark_search(datasets, trees)
    benchmark_sort(datasets)
    benchmark_sort_cases(datasets)
    save_csv()