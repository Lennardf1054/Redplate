# ---------- SEARCHING (find an order by order number) ----------

def linear_search(orders, order_no):
    """Check every order from the start. Works on any list. O(n)."""
    for i, order in enumerate(orders):
        if order["order_no"] == order_no:
            return i
    return -1                                  # not found


def binary_search(orders, order_no):
    """Repeatedly halve the search area. The list MUST be sorted by order_no. O(log n)."""
    low = 0
    high = len(orders) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_no = orders[mid]["order_no"]
        if mid_no == order_no:
            return mid
        elif mid_no < order_no:
            low = mid + 1                      # target is in the right half
        else:
            high = mid - 1                     # target is in the left half
    return -1                                  # not found


# ---------- SORTING (for the sales report) ----------
# Both take a list of dicts and the dict key to sort by (like "total").
# Both return a NEW sorted list and leave the original alone.

def bubble_sort(items, key):
    """Swap neighbors that are out of order, pass after pass. O(n^2)."""
    data = list(items)                         # copy
    n = len(data)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):             # last i items are already in place
            if data[j][key] > data[j + 1][key]:
                data[j], data[j + 1] = data[j + 1], data[j]
                swapped = True
        if not swapped:                        # no swaps means already sorted
            break
    return data


def merge_sort(items, key):
    """Split in half, sort each half, merge them back. O(n log n)."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left, right, key):
    result = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:      # <= keeps equal items in original order
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])                    # one side may have leftovers
    result.extend(right[j:])
    return result