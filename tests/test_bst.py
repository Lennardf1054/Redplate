import unittest
from Back_End.Structures.bst import BST


class TestBST(unittest.TestCase):

    # ---------- NORMAL ----------
    def test_insert_and_search(self):
        t = BST()
        t.insert(50, "order 50")
        t.insert(30, "order 30")
        t.insert(70, "order 70")
        self.assertEqual(t.search(30), "order 30")
        self.assertEqual(t.search(70), "order 70")
        self.assertEqual(t.size(), 3)

    def test_inorder_is_sorted(self):
        t = BST()
        for k in [50, 30, 70, 20, 40, 60, 80]:
            t.insert(k, str(k))
        keys = [k for k, v in t.inorder()]
        self.assertEqual(keys, [20, 30, 40, 50, 60, 70, 80])

    def test_update_existing_key(self):
        t = BST()
        t.insert(5, "Pending")
        t.insert(5, "Ready")
        self.assertEqual(t.search(5), "Ready")
        self.assertEqual(t.size(), 1)       # size must NOT grow

    def test_contains(self):
        t = BST()
        t.insert(10, "x")
        self.assertTrue(t.contains(10))
        self.assertFalse(t.contains(11))

    # ---------- BOUNDARY ----------
    def test_new_tree_is_empty(self):
        t = BST()
        self.assertTrue(t.is_empty())
        self.assertEqual(t.size(), 0)
        self.assertEqual(t.inorder(), [])

    def test_single_node(self):
        t = BST()
        t.insert(1, "only")
        self.assertEqual(t.search(1), "only")
        self.assertEqual(t.inorder(), [(1, "only")])

    def test_sorted_insert_degenerate(self):
        # keys in increasing order make a straight line; must not crash
        t = BST()
        for k in range(1, 2001):
            t.insert(k, k)
        self.assertEqual(t.size(), 2000)
        self.assertEqual(t.search(2000), 2000)
        self.assertEqual(len(t.inorder()), 2000)

    def test_reverse_sorted_insert(self):
        t = BST()
        for k in range(500, 0, -1):
            t.insert(k, k)
        keys = [k for k, v in t.inorder()]
        self.assertEqual(keys, list(range(1, 501)))

    # ---------- INVALID ----------
    def test_search_missing_raises(self):
        t = BST()
        t.insert(1, "a")
        with self.assertRaises(KeyError):
            t.search(99)

    def test_search_empty_raises(self):
        t = BST()
        with self.assertRaises(KeyError):
            t.search(1)

    def test_bad_key_types_raise(self):
        t = BST()
        for bad in ["5", 2.5, None, True]:
            with self.assertRaises(TypeError):
                t.insert(bad, "x")


if __name__ == "__main__":
    unittest.main()