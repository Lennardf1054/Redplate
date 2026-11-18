"""
Queue (FIFO) built from a singly linked list.
Used for pending orders: first come, first served.

    front -> [A] -> [B] -> [C] <- rear
    dequeue takes from the front, enqueue adds at the rear.

Both are O(1). A Python list with pop(0) would be O(n) because every
element has to shift left.
"""


class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Queue:
    def __init__(self):
        self.front = None   # dito nagde-dequeue
        self.rear = None    # dito nag-eenqueue
        self.size = 0

    def is_empty(self):
        return self.front is None

    def enqueue(self, item):
        """Add item at the rear. O(1)."""
        node = Node(item)
        if self.rear is None:          # empty pa: front at rear parehong magbabago
            self.front = node
            self.rear = node
        else:
            self.rear.next = node
            self.rear = node
        self.size += 1

    def dequeue(self):
        """Remove and return the front item. Returns None if empty. O(1)."""
        if self.front is None:
            return None
        node = self.front
        self.front = node.next
        if self.front is None:         # naging empty: rear = None din
            self.rear = None
        self.size -= 1
        return node.data

    def peek(self):
        """Return the front item without removing it. None if empty. O(1)."""
        if self.front is None:
            return None
        return self.front.data

    def remove(self, predicate):
        """Remove the first item for which predicate(item) is True.
        Example: queue.remove(lambda order: order["id"] == 5)
        Returns True if removed, False if not found. O(n)."""
        prev = None
        node = self.front
        while node is not None:
            if predicate(node.data):
                if prev is None:               # front ang tinanggal
                    self.front = node.next
                else:
                    prev.next = node.next
                if node is self.rear:          # rear ang tinanggal: umatras ang rear
                    self.rear = prev
                self.size -= 1
                return True
            prev = node
            node = node.next
        return False

    def to_list(self):
        """All items from front to rear (does not change the queue). O(n)."""
        result = []
        node = self.front
        while node is not None:
            result.append(node.data)
            node = node.next
        return result

    def clear(self):
        self.front = None
        self.rear = None
        self.size = 0

    def __len__(self):
        return self.size