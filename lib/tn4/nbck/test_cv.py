import unittest

from cv import Condition as Cond
from cv import ConditionalValue as CV


def is_equal(a, b):
    return a.value == b.value and a.condition == b.condition


class TestCV(unittest.TestCase):

    def __add_and_assert(self, a, b, x):
        self.assertTrue(is_equal(a+b, x))
        self.assertTrue(is_equal(b+a, x))

    def test_add_is_to_dk(self):
        a = CV({1,2,3}, Cond.IS)
        b = CV(None, Cond.DONTCARE)
        x = CV({1,2,3}, Cond.IS)
        self.__add_and_assert(a, b, x)

    def test_add_is_to_is(self):
        a = CV({1,2,3}, Cond.IS)
        b = CV({1,2,3}, Cond.IS)
        x = CV({1,2,3}, Cond.IS)
        self.__add_and_assert(a, b, x)

    def test_add_is_to_include(self):
        a = CV({1,2,3}, Cond.IS)
        b = CV({1,3}, Cond.INCLUDE)
        x = CV({1,2,3}, Cond.IS)
        self.__add_and_assert(a, b, x)

    def test_add_is_to_included(self):
        a = CV({1,3}, Cond.IS)
        b = CV({1,2,3}, Cond.INCLUDED)
        x = CV({1,3}, Cond.IS)
        self.__add_and_assert(a, b, x)

    def test_add_is_to_exclude(self):
        a = CV({1,3}, Cond.IS)
        b = CV({2}, Cond.EXCLUDE)
        x = CV({1,3}, Cond.IS)
        self.__add_and_assert(a, b, x)

    def test_add_include_to_include(self):
        a = CV({1,2}, Cond.INCLUDE)
        b = CV({1,3}, Cond.INCLUDE)
        x = CV({1,2,3}, Cond.INCLUDE)
        self.__add_and_assert(a, b, x)

    def test_add_include_to_included(self):
        a = CV({1,3}, Cond.INCLUDE)
        b = CV({1,2,3}, Cond.INCLUDED)
        x = CV({1,3}, Cond.INCLUDE)
        self.__add_and_assert(a, b, x)

    def test_add_include_to_exclude(self):
        a = CV({1,3}, Cond.INCLUDE)
        b = CV({2}, Cond.EXCLUDE)
        x = CV({1,3}, Cond.INCLUDE)
        self.__add_and_assert(a, b, x)

    def test_add_included_to_included(self):
        a = CV({1,3}, Cond.INCLUDED)
        b = CV({2,3}, Cond.INCLUDED)
        x = CV({1,2,3}, Cond.INCLUDED)
        self.__add_and_assert(a, b, x)

    def test_add_included_to_exclude(self):
        a = CV({1,2,3}, Cond.INCLUDED)
        b = CV({2}, Cond.EXCLUDE)
        x = CV({1,3}, Cond.INCLUDED)
        self.__add_and_assert(a, b, x)

    def test_add_exclude_to_exclude(self):
        a = CV({1,2}, Cond.EXCLUDE)
        b = CV({1,3}, Cond.EXCLUDE)
        x = CV({1,2,3}, Cond.EXCLUDE)
        self.__add_and_assert(a, b, x)


if __name__ == "__main__":
    unittest.main()
