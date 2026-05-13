import unittest

def add(x, y):
    return x + y


class AddTestCase(unittest.TestCase):
    def test_add_function(self):
        self.assertEqual(add(2, 2), 4)

    def test_concatenation(self):
        self.assertEqual(add('ab', 'xy'), 'abxy')

    def test_add_function_(self):
        self.assertNotEqual(add(10, 13), 5)


if __name__ == '__main__':
    unittest.main()