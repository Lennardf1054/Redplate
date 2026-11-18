class MinHeap:
    def __init__(self):
        self._data = []          # the tree lives in a plain list

    def is_empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek at an empty heap")
        return self._data[0]     # smallest item is always at index 0

    def push(self, item):
        self._data.append(item)                  # add at the end
        self._sift_up(len(self._data) - 1)       # then fix its position

    def pop(self):
        if self.is_empty():
            raise IndexError("Cannot pop from an empty heap")
        root = self._data[0]         # save the smallest item
        last = self._data.pop()      # remove the last item from the list
        if not self.is_empty():      # if anything is left...
            self._data[0] = last     # ...the last item takes the root's place
            self._sift_down(0)       # then sinks to where it belongs
        return root

    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self._data[i] < self._data[parent]:
                self._data[i], self._data[parent] = self._data[parent], self._data[i]
                i = parent           # keep checking from the new spot
            else:
                break                # already in a good spot

    def _sift_down(self, i):
        n = len(self._data)
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2
            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right
            if smallest == i:
                break                # no child is smaller, done
            self._data[i], self._data[smallest] = self._data[smallest], self._data[i]
            i = smallest             # keep sinking