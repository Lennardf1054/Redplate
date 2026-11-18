class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Queue:
    def __init__(self):
        self.front = None   # first in line (next to be served)
        self.back = None    # last in line (newest)
        self._size = 0

    def is_empty(self):
        return self.front is None

    def size(self):
        return self._size

    def enqueue(self, item):
        new_node = Node(item)
        if self.is_empty():
            # first item: it's both the front and the back
            self.front = new_node
            self.back = new_node
        else:
            self.back.next = new_node   # link the old back to the new node
            self.back = new_node        # new node is now the back
        self._size += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty queue")
        data = self.front.data
        self.front = self.front.next    # move front to the next node
        if self.front is None:
            self.back = None            # queue is now empty
        self._size -= 1
        return data

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek at an empty queue")
        return self.front.data