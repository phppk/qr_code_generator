version = 3
error_correction_level = "L"
total_nr_codewords = 55
mode = "0100" # byteMode
char_count_indicator_len = 8
bin = lambda x : ''.join(reversed([str((x >> i) & 1) for i in range(char_count_indicator_len)]))

# Stack Class selbst implementiert feur mehr "Typsicherheit"
class Stack:
    def __init__(self):
        self.stack = []

    def push(self, element):
        self.stack.append(element)

    def pop(self):
        if self.isEmpty():
            return "Stack is Empty."
        return self.stack.pop()
    
    def peek(self):
        if self.isEmpty():
            return "Stack is Empty."
        return self.stack[-1]
    
    def isEmpty(self):
        return len(self.stack) == 0
    
    def size(self):
        return len(self.stack)