import unittest
from Back_End.Structures.stack import Stack


class TestStack(unittest.TestCase):

    # ---------- NORMAL ----------
    def test_lifo_order(self):
        s = Stack()
        s.push("A")
        s.push("B")
        s.push("C")
        self.assertEqual(s.pop(), "C")   # last in, first out
        self.assertEqual(s.pop(), "B")
        self.assertEqual(s.size(), 1)

    def test_peek_does_not_remove(self):
        s = Stack()
        s.push(10)
        self.assertEqual(s.peek(), 10)
        self.assertEqual(s.size(), 1)

    # ---------- BOUNDARY ----------
    def test_new_stack_is_empty(self):
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(s.size(), 0)

    def test_push_after_emptied(self):
        s = Stack()
        s.push(1)
        s.pop()
        self.assertTrue(s.is_empty())
        s.push(9)
        self.assertEqual(s.peek(), 9)

    # ---------- INVALID ----------
    def test_pop_empty_raises(self):
        s = Stack()
        with self.assertRaises(IndexError):
            s.pop()

    def test_peek_empty_raises(self):
        s = Stack()
        with self.assertRaises(IndexError):
            s.peek()


if __name__ == "__main__":
    unittest.main()