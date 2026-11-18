import unittest
from Back_End.Structures.heap import MinHeap


class TestMinHeap(unittest.TestCase):

    # ---------- NORMAL ----------
    def test_pops_in_sorted_order(self):
        h = MinHeap()
        for x in [5, 3, 8, 1]:
            h.push(x)
        self.assertEqual([h.pop() for _ in range(4)], [1, 3, 5, 8])

    def test_lower_priority_first(self):
        h = MinHeap()
        h.push((2, 10))      # (priority, order_no)
        h.push((1, 11))
        self.assertEqual(h.pop(), (1, 11))

    def test_tie_goes_to_older_order(self):
        h = MinHeap()
        h.push((1, 12))
        h.push((1, 10))
        self.assertEqual(h.pop(), (1, 10))

    def test_peek_does_not_remove(self):
        h = MinHeap()
        h.push(4)
        self.assertEqual(h.peek(), 4)
        self.assertEqual(h.size(), 1)

    # ---------- BOUNDARY ----------
    def test_new_heap_is_empty(self):
        h = MinHeap()
        self.assertTrue(h.is_empty())
        self.assertEqual(h.size(), 0)

    def test_single_item(self):
        h = MinHeap()
        h.push(7)
        self.assertEqual(h.pop(), 7)
        self.assertTrue(h.is_empty())

    def test_duplicates(self):
        h = MinHeap()
        for x in [2, 2, 1, 1]:
            h.push(x)
        self.assertEqual([h.pop() for _ in range(4)], [1, 1, 2, 2])

    def test_push_after_emptied(self):
        h = MinHeap()
        h.push(1)
        h.pop()
        h.push(5)
        self.assertEqual(h.peek(), 5)

    def test_many_items_sorted(self):
        data = [9, 4, 7, 1, 8, 2, 6, 3, 5, 0]
        h = MinHeap()
        for x in data:
            h.push(x)
        self.assertEqual([h.pop() for _ in range(len(data))], sorted(data))

    # ---------- INVALID ----------
    def test_pop_empty_raises(self):
        h = MinHeap()
        with self.assertRaises(IndexError):
            h.pop()

    def test_peek_empty_raises(self):
        h = MinHeap()
        with self.assertRaises(IndexError):
            h.peek()


if __name__ == "__main__":
    unittest.main()