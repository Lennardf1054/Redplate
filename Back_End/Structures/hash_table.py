class HashTable:
    def __init__(self, capacity=16):
        self._capacity = capacity
        self._buckets = [[] for _ in range(capacity)]   # each bucket holds (key, value) pairs
        self._size = 0

    def size(self):
        return self._size

    def _hash(self, key):
        # bool is a subclass of int in Python, so reject it explicitly
        if isinstance(key, bool):
            raise TypeError("Key must be int or str")
        if isinstance(key, int):
            return key % self._capacity
        if isinstance(key, str):
            total = 0
            for ch in key:
                total = total * 31 + ord(ch)
            return total % self._capacity
        raise TypeError("Key must be int or str")

    def put(self, key, value):
        index = self._hash(key)              # also validates the key type
        bucket = self._buckets[index]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)     # key exists: update, size unchanged
                return
        bucket.append((key, value))          # new key: add to the chain
        self._size += 1

    def get(self, key):
        bucket = self._buckets[self._hash(key)]
        for k, v in bucket:
            if k == key:
                return v
        raise KeyError(key)

    def contains(self, key):
        bucket = self._buckets[self._hash(key)]
        for k, v in bucket:
            if k == key:
                return True
        return False

    def remove(self, key):
        bucket = self._buckets[self._hash(key)]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return
        raise KeyError(key)

    def items(self):
        result = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append(pair)
        return result