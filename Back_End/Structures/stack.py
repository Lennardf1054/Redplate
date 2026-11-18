"""
Stack (LIFO) built from a singly linked list.
Used for the cart's Undo: every cart action is pushed, and Undo pops the
most recent one and reverses it.

    top -> [C] -> [B] -> [A]
    push and pop both work on the top, so both are O(1).
"""


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    def __init__(self):
        self.top = None
        self.size = 0

    def is_empty(self):
        return self.top is None

    def push(self, item):
        """Put item on top. O(1)."""
        node = Node(item)
        node.next = self.top        # ang dating top ay nasa ilalim na ng bago
        self.top = node
        self.size += 1

    def pop(self):
        """Remove and return the top item. Returns None if empty. O(1)."""
        if self.top is None:
            return None
        node = self.top
        self.top = node.next
        self.size -= 1
        return node.data

    def peek(self):
        """Return the top item without removing it. None if empty. O(1)."""
        if self.top is None:
            return None
        return self.top.data

    def to_list(self):
        """All items from top to bottom (does not change the stack). O(n)."""
        result = []
        node = self.top
        while node is not None:
            result.append(node.data)
            node = node.next
        return result

    def clear(self):
        self.top = None
        self.size = 0

    def __len__(self):
        return self.size