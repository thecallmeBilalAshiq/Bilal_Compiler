# regalloc.py

class RegisterAllocator:
    def __init__(self):
        # x86-64 caller-saved for simplicity
        self.free_regs = ['rax', 'rbx', 'rcx', 'rdx']
        self.locations = {}      # temp → register or stack offset
        self.next_slot = 0       # in bytes, grows by 8

    def reset(self):
        self.free_regs = ['rax', 'rbx', 'rcx', 'rdx']
        self.locations.clear()
        self.next_slot = 0

    def allocate(self, name):
        """
        Assign a location (reg or [rbp - offset]) to 'name'.
        Returns the location string.
        """
        if name in self.locations:
            return self.locations[name]

        if self.free_regs:
            loc = self.free_regs.pop(0)
        else:
            # spill to stack: allocate an 8-byte slot
            offset = self.next_slot + 8
            self.next_slot = offset
            loc = f"[rbp-{offset}]"
        self.locations[name] = loc
        return loc

    def get_location(self, name):
        # If we haven't seen this name yet, allocate it
        if name not in self.locations:
            self.allocate(name)
        return self.locations[name]

    def allocate_stack_slot(self, name):
        """
        Forcefully allocate a new stack slot for 'name', even if already assigned.
        Returns the raw offset (e.g., 8, 16, 24), not wrapped in [rbp-...].
        """
        offset = self.next_slot + 8
        self.next_slot = offset
        self.locations[name] = f"[rbp-{offset}]"
        return offset

    def stack_size(self):
        """Total bytes to subtract from RSP in prologue."""
        # round up to 16-byte alignment
        sz = ((self.next_slot + 15) // 16) * 16
        return sz
