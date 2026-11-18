from Back_End.Structures.stack import Stack


class BSTNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class BST:
    def __init__(self):
        self.root = None
        self._size = 0

    def is_empty(self):
        return self.root is None

    def size(self):
        return self._size

    def _check_key(self, key):
        # bool counts as int in Python, so reject it explicitly
        if isinstance(key, bool) or not isinstance(key, int):
            raise TypeError("Key must be an int")

    def insert(self, key, value):
        self._check_key(key)
        if self.root is None:                    # empty tree: new node is the root
            self.root = BSTNode(key, value)
            self._size += 1
            return
        current = self.root
        while True:
            if key == current.key:               # key exists: update only
                current.value = value
                return
            if key < current.key:                # smaller keys go left
                if current.left is None:
                    current.left = BSTNode(key, value)
                    self._size += 1
                    return
                current = current.left
            else:                                # bigger keys go right
                if current.right is None:
                    current.right = BSTNode(key, value)
                    self._size += 1
                    return
                current = current.right

    def search(self, key):
        self._check_key(key)
        current = self.root
        while current is not None:
            if key == current.key:
                return current.value
            if key < current.key:
                current = current.left
            else:
                current = current.right
        raise KeyError(key)                      # fell off the tree: not found

    def contains(self, key):
        try:
            self.search(key)
            return True
        except KeyError:
            return False

    def inorder(self):
        result = []
        stack = Stack()
        current = self.root
        while current is not None or not stack.is_empty():
            while current is not None:           # go as far left as possible
                stack.push(current)
                current = current.left
            current = stack.pop()                # visit the node
            result.append((current.key, current.value))
            current = current.right              # then explore its right side
        return result