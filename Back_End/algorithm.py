import random
from Back_End.algorithm import linear_search, binary_search, bubble_sort, merge_sort

def make_orders(ids):
    return [{"id": i, "total": i * 10} for i in ids]

# --- search ---
def test_search_found():
    orders = make_orders([1, 2, 3, 4, 5])
    assert linear_search(orders, 3)["id"] == 3
    assert binary_search(orders, 3)["id"] == 3

def test_search_not_found():
    orders = make_orders([1, 2, 3])
    assert linear_search(orders, 99) is None
    assert binary_search(orders, 99) is None

def test_search_boundaries():
    orders = make_orders([1, 2, 3, 4, 5])
    for algo in (linear_search, binary_search):
        assert algo(orders, 1)["id"] == 1
        assert algo(orders, 5)["id"] == 5

def test_search_empty_and_single():
    for algo in (linear_search, binary_search):
        assert algo([], 1) is None
        assert algo(make_orders([7]), 7)["id"] == 7

# --- sort ---
def test_sorts_match():
    orders = [{"id": 1, "total": 50}, {"id": 2, "total": 10}, {"id": 3, "total": 30}]
    for algo in (bubble_sort, merge_sort):
        assert [o["total"] for o in algo(orders, "total")] == [10, 30, 50]

def test_sort_does_not_mutate_original():
    for algo in (bubble_sort, merge_sort):
        orders = [{"id": 1, "total": 50}, {"id": 2, "total": 10}]
        algo(orders, "total")
        assert orders[0]["total"] == 50

def test_sort_reverse_and_edge_cases():
    for algo in (bubble_sort, merge_sort):
        assert algo([], "total") == []
        one = [{"id": 1, "total": 5}]
        assert algo(one, "total") == one
        orders = [{"id": 1, "total": 1}, {"id": 2, "total": 3}, {"id": 3, "total": 2}]
        assert [o["total"] for o in algo(orders, "total", reverse=True)] == [3, 2, 1]

def test_sort_stable_with_duplicates():
    orders = [{"id": 1, "total": 5}, {"id": 2, "total": 5}, {"id": 3, "total": 1}]
    for algo in (bubble_sort, merge_sort):
        assert [o["id"] for o in algo(orders, "total")] == [3, 1, 2]

def test_random_data_matches_builtin():
    random.seed(1)
    orders = [{"id": i, "total": random.randint(1, 100)} for i in range(300)]
    expected = [o["total"] for o in sorted(orders, key=lambda o: o["total"])]
    for algo in (bubble_sort, merge_sort):
        assert [o["total"] for o in algo(orders, "total")] == expected