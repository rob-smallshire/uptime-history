import struct
from mmap import mmap, PROT_WRITE, PROT_READ

BITS_PER_BYTE = 8
WORD = "Q"  # 64-bit unsigned integer

class DailyReliabilityHistory:
    """Store a per-customer daily record of equipment reliability

    For each customer maintain a daily record of whether their
    Internet connection equipment (e.g. cable modem) experienced
    a fault or not on that day.
    """

    @classmethod
    def create(cls, filepath, num_customers):
        zero = struct.pack(WORD, 0)
        with open(filepath, "wb") as file:
            for _ in range(num_customers):
                file.write(zero)
        return cls(filepath)

    def __init__(self, filepath):
        self._filepath = filepath
        self._file = open(self._filepath, "a+b")
        self._mmap = mmap(self._file.fileno(), 0, PROT_WRITE | PROT_READ)
        self._byteview = memoryview(self._mmap)
        self._wordview = self._byteview.cast(WORD)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        del self._wordview
        del self._byteview
        self._mmap.flush()
        self._mmap.close()
        self._file.close()

    @property
    def num_customers(self):
        return len(self._wordview)

    @property
    def record_duration_days(self):
        return struct.calcsize(WORD) * BITS_PER_BYTE

    def _customer_history(self, customer_id):
        if not (0 <= customer_id < self.num_customers):
            raise ValueError(f"customer id {customer_id} out of range")
        return self._wordview[customer_id]

    def register(self, customer_id, experienced_fault):
        history = self._customer_history(customer_id)
        b = bool(experienced_fault)
        history >>= 1
        msb = self.record_duration_days - 1
        bit =  b << msb
        history |= bit
        self._wordview[customer_id] = history

    def was_reliable(self, customer_id, num_days_ago):
        history = self._customer_history(customer_id)
        if not (0 <= num_days_ago < self.record_duration_days):
            raise ValueError("day number {num_days_ago} out of range")
        bit_number = (self.record_duration_days - 1) - num_days_ago
        mask = 1 << bit_number
        return not bool(history & mask)

    def num_fault_days(self, customer_id):
        history = self._customer_history(customer_id)
        n = 0
        while history:
            n += 1
            history &= history - 1
        return n

    def longest_fault_duration_days(self, customer_id):
        history = self._customer_history(customer_id)
        n = 0
        while history:
            n += 1
            history &= history >> 1
        return n

r = DailyReliabilityHistory("reliability.dat")

import code
code.interact(local=locals())

print("Done!")
