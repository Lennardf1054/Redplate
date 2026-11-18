import unittest
from Back_End.Structures.queue import Queue


class TestQueue(unittest.TestCase):

    # ---------- NORMAL ----------
    def test_fifo_order(self):
        q = Queue()
        q.enqueue("A")
        q.enqueue("B")
        q.enqueue("C")
        self.assertEqual(q.dequeue(), "A")
        self.assertEqual(q.dequeue(), "B")
        self.assertEqual(q.size(), 1)

    def test_peek_does_not_remove(self):
        q = Queue()
        q.enqueue(10)
        self.assertEqual(q.peek(), 10)
        self.assertEqual(q.size(), 1)

    # ---------- BOUNDARY ----------
    def test_new_queue_is_empty(self):
        q = Queue()
        self.assertTrue(q.is_empty())
        self.assertEqual(q.size(), 0)

    def test_enqueue_after_emptied(self):
        q = Queue()
        q.enqueue(1)
        q.dequeue()
        self.assertTrue(q.is_empty())
        q.enqueue(9)
        self.assertEqual(q.peek(), 9)

    # ---------- INVALID ----------
    def test_dequeue_empty_raises(self):
        q = Queue()
        with self.assertRaises(IndexError):
            q.dequeue()

    def test_peek_empty_raises(self):
        q = Queue()
        with self.assertRaises(IndexError):
            q.peek()


if __name__ == "__main__":
    unittest.main()