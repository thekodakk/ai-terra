import unittest
from hesap import ortalama


class OrtalamaTests(unittest.TestCase):
    def test_ortalama(self):
        self.assertEqual(ortalama([2, 4, 6]), 4)

    def test_bos_liste(self):
        with self.assertRaises(ValueError):
            ortalama([])


if __name__ == '__main__':
    unittest.main()
