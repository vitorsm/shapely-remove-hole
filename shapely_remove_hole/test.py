import json
from shapely.geometry import shape, Polygon


def load_shape(file_path: str) -> Polygon:
    file = open(file_path, "r")
    geo_dict = json.load(file)
    file.close()
    return shape(geo_dict["geometry"])


def test():
    geom1 = shape(load_shape("../resources/input_polygon1.json"))
    geom2 = shape(load_shape("../resources/input_polygon2.json"))

    print(f"compare: {geom2.within(geom1)}")


if __name__ == "__main__":
    test()
