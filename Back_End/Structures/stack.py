class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Stack:
    def __init__(self):
        self.top = None      # the newest item (top of the pile)
        self._size = 0

    def is_empty(self):
        return self.top is None

    def size(self):
        return self._size

    def push(self, item):
        new_node = Node(item)
        new_node.next = self.top   # new node points down to the old top
        self.top = new_node        # new node becomes the top
        self._size += 1

    def pop(self):
        if self.is_empty():
            raise IndexError("Cannot pop from an empty stack")
        data = self.top.data       # save the data before we move away
        self.top = self.top.next   # top moves down one node
        self._size -= 1
        return data

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek at an empty stack")
        return self.top.data