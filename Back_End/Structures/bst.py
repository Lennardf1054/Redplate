"""
Binary Search Tree: stores all order records, keyed by order ID.
key   = order id (int)
value = the order dict

Everything is ITERATIVE (loops, no recursion). Order IDs keep increasing,
so the tree leans to one side (like a linked list). A recursive version
would crash with RecursionError at around 1000 orders.
"""


class BSTNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None     # smaller keys
        self.right = None    # bigger keys


class BST:
    def __init__(self):
        self.root = None
        self.size = 0

    def is_empty(self):
        return self.root is None

    def __len__(self):
        return self.size

    # ---------- INSERT ----------
    def insert(self, key, value):
        """Add a new record. If the key already exists, update its value.
        Returns True if a new node was added, False if it was an update."""
        if key is None:
            raise ValueError("key cannot be None")

        if self.root is None:
            self.root = BSTNode(key, value)
            self.size += 1
            return True

        cur = self.root
        while True:
            if key == cur.key:
                cur.value = value          # duplicate: update only
                return False
            elif key < cur.key:
                if cur.left is None:
                    cur.left = BSTNode(key, value)
                    self.size += 1
                    return True
                cur = cur.left
            else:
                if cur.right is None:
                    cur.right = BSTNode(key, value)
                    self.size += 1
                    return True
                cur = cur.right

    # ---------- SEARCH ----------
    def search(self, key):
        """Return the value for key, or None if not found."""
        cur = self.root
        while cur is not None:
            if key == cur.key:
                return cur.value
            elif key < cur.key:
                cur = cur.left
            else:
                cur = cur.right
        return None

    def contains(self, key):
        cur = self.root
        while cur is not None:
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    # ---------- DELETE ----------
    def delete(self, key):
        """Remove the node with this key. Returns True if removed, False if not found."""
        # 1. hanapin ang node (at ang parent nito)
        parent = None
        cur = self.root
        while cur is not None and cur.key != key:
            parent = cur
            cur = cur.left if key < cur.key else cur.right

        if cur is None:
            return False

        # 2. Case: dalawang anak. Palitan ng inorder successor
        #    (pinakamaliit sa kanang subtree), tapos yung successor na ang buburahin.
        if cur.left is not None and cur.right is not None:
            succ_parent = cur
            succ = cur.right
            while succ.left is not None:
                succ_parent = succ
                succ = succ.left
            cur.key = succ.key
            cur.value = succ.value
            parent = succ_parent
            cur = succ                 # successor ay may max na isang anak (kanan)

        # 3. Case: 0 o 1 anak. Ipalit ang anak (o None) sa pwesto ng node.
        child = cur.left if cur.left is not None else cur.right

        if parent is None:
            self.root = child
        elif parent.left is cur:
            parent.left = child
        else:
            parent.right = child

        self.size -= 1
        return True

    # ---------- TRAVERSAL ----------
    def inorder(self):
        """All values sorted by key (ascending). Iterative traversal.
        Left -> Node -> Right."""
        result = []
        stack = []                     # helper lang para sa traversal
        cur = self.root
        while stack or cur is not None:
            while cur is not None:     # pumunta sa pinakakaliwa
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            result.append(cur.value)
            cur = cur.right
        return result

    def height(self):
        """Number of levels (empty tree = 0). Useful to show the skew problem."""
        if self.root is None:
            return 0
        best = 0
        stack = [(self.root, 1)]
        while stack:
            node, depth = stack.pop()
            if depth > best:
                best = depth
            if node.left is not None:
                stack.append((node.left, depth + 1))
            if node.right is not None:
                stack.append((node.right, depth + 1))
        return best