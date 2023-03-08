import unittest

from cv import Condition as Cond
from cv import ConditionalValue as CV


def is_equal(a, b):
    return a.value == b.value and a.condition == b.condition


class TestCV(unittest.TestCase):

    def test_add_is_to_is(self):
        a = CV({1,2,3}, Cond.IS)
        b = CV({1,2,3}, Cond.IS)
        x = CV({1,2,3}, Cond.IS)
        self.assertTrue(is_equal(a+b, x))


if __name__ == "__main__":
    unittest.main()
