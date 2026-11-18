import unittest
from Back_End.Structures.hash_table import HashTable


class TestHashTable(unittest.TestCase):

    # ---------- NORMAL ----------
    def test_put_and_get(self):
        h = HashTable()
        h.put(1, "Chicken Adobo")
        self.assertEqual(h.get(1), "Chicken Adobo")

    def test_string_keys(self):
        h = HashTable()
        h.put("Iced Tea", 20)
        h.put("Pancit Canton", 35)
        self.assertEqual(h.get("Iced Tea"), 20)
        self.assertEqual(h.get("Pancit Canton"), 35)

    def test_update_existing_key(self):
        h = HashTable()
        h.put(1, 60)
        h.put(1, 65)                       # same key, new value
        self.assertEqual(h.get(1), 65)
        self.assertEqual(h.size(), 1)      # size must NOT grow

    def test_remove_then_contains_false(self):
        h = HashTable()
        h.put(1, "A")
        h.remove(1)
        self.assertFalse(h.contains(1))
        self.assertEqual(h.size(), 0)

    def test_items_returns_all_pairs(self):
        h = HashTable()
        h.put(1, "A")
        h.put(2, "B")
        h.put(3, "C")
        self.assertEqual(sorted(h.items()), [(1, "A"), (2, "B"), (3, "C")])

    # ---------- BOUNDARY ----------
    def test_new_table_is_empty(self):
        h = HashTable()
        self.assertEqual(h.size(), 0)
        self.assertEqual(h.items(), [])

    def test_contains_missing_is_false(self):
        h = HashTable()
        self.assertFalse(h.contains(99))

    def test_collision_both_readable(self):
        h = HashTable(16)
        h.put(1, "first")                  # 1 % 16 = 1
        h.put(17, "second")                # 17 % 16 = 1 -> same bucket
        self.assertEqual(h.get(1), "first")
        self.assertEqual(h.get(17), "second")
        self.assertEqual(h.size(), 2)

    def test_remove_one_of_colliding_keys(self):
        h = HashTable(16)
        h.put(1, "first")
        h.put(17, "second")
        h.remove(1)
        self.assertFalse(h.contains(1))
        self.assertEqual(h.get(17), "second")   # the other one survives
        self.assertEqual(h.size(), 1)

    def test_many_items(self):
        h = HashTable()
        for i in range(100):
            h.put(i, i * 10)
        self.assertEqual(h.size(), 100)
        for i in range(100):
            self.assertEqual(h.get(i), i * 10)

    # ---------- INVALID ----------
    def test_get_missing_raises(self):
        h = HashTable()
        with self.assertRaises(KeyError):
            h.get(5)

    def test_remove_missing_raises(self):
        h = HashTable()
        with self.assertRaises(KeyError):
            h.remove(5)

    def test_float_key_raises(self):
        h = HashTable()
        with self.assertRaises(TypeError):
            h.put(1.5, "x")

    def test_none_key_raises(self):
        h = HashTable()
        with self.assertRaises(TypeError):
            h.put(None, "x")


if __name__ == "__main__":
    unittest.main()