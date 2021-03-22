import unittest
from shapely_remove_hole import main

FILE_PATH1 = f"../resources/input1.json"
FILE_PATH2 = f"../resources/input2.json"
FILE_PATH3 = f"../resources/input3.json"
FILE_PATH4 = f"../resources/input4.json"

FILE_PATHS = [FILE_PATH1, FILE_PATH2, FILE_PATH3, FILE_PATH4]


class TestRemoveHole(unittest.TestCase):

    def test_remove(self):
        for file_path in FILE_PATHS:
            print(f"will test {file_path}")
            geom = main.load_shape(file_path)
            result = main.remove_hole(geom)

            self.assertTrue(result.is_valid)
            self.assertTrue(not result.interiors)

