import random
from Back_End.algorithm import linear_search, binary_search, bubble_sort, merge_sort


def make_orders(n):
    return [{"order_no": i, "total": random.randint(20, 500)} for i in range(1, n + 1)]


def test_search():
    orders = make_orders(10)
    for search in (linear_search, binary_search):
        assert search(orders, 1) == 0                  # first (boundary)
        assert search(orders, 10) == 9                 # last (boundary)
        assert search(orders, 5) == 4                  # middle (normal)
        assert search(orders, 999) == -1               # missing (invalid)
        assert search(orders, 0) == -1
        assert search([], 1) == -1                     # empty list
        assert search([{"order_no": 7}], 7) == 0       # one item


def test_sort():
    for sort in (bubble_sort, merge_sort):
        data = make_orders(200)
        expected = sorted(data, key=lambda o: o["total"])
        result = sort(data, "total")
        assert [o["total"] for o in result] == [o["total"] for o in expected]
        assert sort([], "total") == []                              # empty
        assert sort([{"total": 5}], "total") == [{"total": 5}]      # one item
        same = [{"total": 3}, {"total": 3}, {"total": 3}]
        assert sort(same, "total") == same                          # duplicates
        original = make_orders(20)
        copy = list(original)
        sort(original, "total")
        assert original == copy                                     # input not changed


if __name__ == "__main__":
    test_search()
    test_sort()
    print("All algorithm tests passed")