class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class Queue:
    def __init__(self):
        self.front = None
        self.back = None
        self._size = 0

    def is_empty(self):
        # TODO: return True if the queue has no items
        pass

    def enqueue(self, item):
        # TODO:
        # 1. make a new Node with item
        # 2. if the queue is empty, front and back both point to it
        # 3. otherwise, link it after back, then move back to it
        # 4. add 1 to _size
        pass

    def dequeue(self):
        # TODO:
        # 1. if empty, raise an error (IndexError with a clear message)
        # 2. save the front node's data
        # 3. move front to front.next
        # 4. if front is now None, set back to None too
        # 5. subtract 1 from _size, return the saved data
        pass

    def peek(self):
        # TODO: return the front's data without removing it (error if empty)
        pass

    def size(self):
        # TODO: return _size
        pass