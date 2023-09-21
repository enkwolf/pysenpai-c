import random

def gen_random_binary(bits):
    """
    gen_random_binary(bits) -> str

    This convenience function creates a randomized string with the given number
    of *bits*. Useful for testing functions that perform bitwise operations.
    """

    i = random.randint(0, 2 ** bits - 1)
    return bin(i)[2:].rjust(bits, "0")

