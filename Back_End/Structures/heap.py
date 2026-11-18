"""
Min-Heap (priority queue) for urgent / long-waiting orders.

LOWER priority number = served FIRST (e.g. 0 = urgent, 1 = normal).
You can also use a timestamp as the priority: the oldest order comes out first.

Stored as an array (Python list) using the usual heap layout:
    parent of i      = (i - 1) // 2
    left child of i  = 2 * i + 1
    right child of i = 2 * i + 2

Each entry is (priority, seq, item). `seq` is an insertion counter used as a
tie-breaker, so orders with the SAME priority come out first-in-first-out.
"""


class MinHeap:
    def __init__(self):
        self.data = []
        self._counter = 0       # tie-breaker para sa pareho ang priority

    # ---------- helpers ----------
    def _less(self, i, j):
        """True if entry at index i should come out before entry at index j."""
        a = self.data[i]
        b = self.data[j]
        if a[0] != b[0]:
            return a[0] < b[0]
        return a[1] < b[1]

    def _swap(self, i, j):
        self.data[i], self.data[j] = self.data[j], self.data[i]

    def _sift_up(self, i):
        """Move entry up while it is smaller than its parent."""
        while i > 0:
            parent = (i - 1) // 2
            if self._less(i, parent):
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i):
        """Move entry down while a child is smaller than it."""
        n = len(self.data)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            smallest = i
            if left < n and self._less(left, smallest):
                smallest = left
            if right < n and self._less(right, smallest):
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    # ---------- main operations ----------
    def push(self, priority, item):
        """Add an item. O(log n)."""
        if isinstance(priority, bool) or not isinstance(priority, (int, float)):
            raise TypeError("priority must be a number")
        self.data.append((priority, self._counter, item))
        self._counter += 1
        self._sift_up(len(self.data) - 1)

    def pop(self):
        """Remove and return the item with the lowest priority number.
        Returns None if the heap is empty. O(log n)."""
        if not self.data:
            return None
        top = self.data[0]
        last = self.data.pop()
        if self.data:                   # may natira pa: ilagay ang last sa root
            self.data[0] = last
            self._sift_down(0)
        return top[2]

    def peek(self):
        """Look at the next item without removing it. None if empty. O(1)."""
        if not self.data:
            return None
        return self.data[0][2]

    def remove(self, predicate):
        """Remove the first item for which predicate(item) is True.
        Example: heap.remove(lambda order: order["id"] == 5)
        Returns True if removed, False if not found. O(n)."""
        idx = -1
        for i in range(len(self.data)):
            if predicate(self.data[i][2]):
                idx = i
                break
        if idx == -1:
            return False

        last = self.data.pop()
        if idx < len(self.data):        # hindi pala yung huli ang tinanggal
            self.data[idx] = last
            self._sift_up(idx)
            self._sift_down(idx)
        return True

    def to_list(self):
        """All items in the order they would be served (does NOT change the heap).
        O(n log n). Used by the admin dashboard."""
        copy = MinHeap()
        copy.data = self.data[:]
        result = []
        while copy.data:
            result.append(copy.pop())
        return result

    def is_empty(self):
        return len(self.data) == 0

    def __len__(self):
        return len(self.data)