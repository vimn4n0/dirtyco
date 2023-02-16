import random
import string


class RandomUtils(object):
    @classmethod
    def rand_string(cls, n=12, omit=None):
        seq = string.ascii_lowercase + string.ascii_uppercase + string.digits
        if omit:
            seq = list(set(seq) - set(omit))
        return "".join(random.choice(seq) for _ in range(n))
