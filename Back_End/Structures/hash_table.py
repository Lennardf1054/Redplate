"""
Hash Table (separate chaining) used for the menu (item_id -> item) and the
cart (item_id -> quantity).

- Keys can be int or str (item IDs, session IDs, item names).
- We write our own hash function (we do NOT use Python's built-in hash()).
- Collisions are handled with chaining: each bucket is a small linked list.
- The table doubles in size when it gets too full, so lookups stay fast.
"""


class HashNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class HashTable:
    LOAD_FACTOR_LIMIT = 0.75

    def __init__(self, capacity=8):
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.buckets = [None] * capacity
        self.size = 0

    # ---------- helpers ----------
    def _hash(self, key):
        """Turn a key into a bucket index (0 to capacity - 1)."""
        if isinstance(key, bool):
            raise TypeError("key must be int or str")
        if isinstance(key, int):
            return key % self.capacity          # Python: laging non-negative
        if isinstance(key, str):
            h = 5381                            # djb2 string hash
            for ch in key:
                h = ((h * 33) + ord(ch)) & 0xFFFFFFFF
            return h % self.capacity
        raise TypeError("key must be int or str")

    def _resize(self):
        """Double the capacity and move every node to its new bucket."""
        old_buckets = self.buckets
        self.capacity *= 2
        self.buckets = [None] * self.capacity

        for head in old_buckets:
            node = head
            while node is not None:
                next_node = node.next           # i-save bago baguhin ang node.next
                idx = self._hash(node.key)
                node.next = self.buckets[idx]   # ilagay sa unahan ng bagong bucket
                self.buckets[idx] = node
                node = next_node

    # ---------- main operations ----------
    def put(self, key, value):
        """Add or update. Returns True if new key, False if it updated an existing key."""
        idx = self._hash(key)

        node = self.buckets[idx]
        while node is not None:
            if node.key == key:
                node.value = value              # existing key: update lang
                return False
            node = node.next

        new_node = HashNode(key, value)         # bagong key: ilagay sa unahan ng chain
        new_node.next = self.buckets[idx]
        self.buckets[idx] = new_node
        self.size += 1

        if self.size / self.capacity > self.LOAD_FACTOR_LIMIT:
            self._resize()
        return True

    def get(self, key, default=None):
        """Return the value for key, or default if not found."""
        node = self.buckets[self._hash(key)]
        while node is not None:
            if node.key == key:
                return node.value
            node = node.next
        return default

    def contains(self, key):
        node = self.buckets[self._hash(key)]
        while node is not None:
            if node.key == key:
                return True
            node = node.next
        return False

    def remove(self, key):
        """Delete a key. Returns True if removed, False if not found."""
        idx = self._hash(key)
        prev = None
        node = self.buckets[idx]

        while node is not None:
            if node.key == key:
                if prev is None:
                    self.buckets[idx] = node.next   # head ng chain ang tinanggal
                else:
                    prev.next = node.next
                self.size -= 1
                return True
            prev = node
            node = node.next
        return False

    # ---------- listing ----------
    def items(self):
        """List of (key, value) pairs. Order is not guaranteed."""
        result = []
        for head in self.buckets:
            node = head
            while node is not None:
                result.append((node.key, node.value))
                node = node.next
        return result

    def keys(self):
        return [k for k, _ in self.items()]

    def values(self):
        return [v for _, v in self.items()]

    def is_empty(self):
        return self.size == 0

    def clear(self):
        self.buckets = [None] * self.capacity
        self.size = 0

    def __len__(self):
        return self.size