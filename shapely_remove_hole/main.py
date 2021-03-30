import json
from typing import List, Tuple

from shapely.geometry import shape, Polygon, LinearRing, Point, LineString
from shapely.geometry.base import BaseGeometry


def load_shape(file_path: str) -> Polygon:
    file = open(file_path, "r")
    geo_dict = json.load(file)
    return shape(geo_dict["features"][0]["geometry"])


def persist_geom(geom: BaseGeometry):
    file = open("resources/output.json", "w")
    json.dump({
        "type": "FeatureCollection",
        "features": [{
            "geometry": geom.__geo_interface__,
            "type": "Feature",
            "properties": {}
        }]
    }, file)


def get_external_polygon(geom: Polygon) -> Polygon:
    return Polygon(LinearRing(geom.exterior.coords))


def get_holes_geometry(geom: Polygon) -> List[Polygon]:
    return [Polygon(LinearRing(hole.coords)) for hole in geom.interiors]


def get_nearest_point_to_point(coordinates: List[Tuple[float, float]],
                               point: Tuple[float, float]) -> Tuple[float, float]:
    p = Point(point)
    distances = [Point(c).distance(p) for c in coordinates]
    distance = 0
    index = 0
    for i, d in enumerate(distances):
        if distance == 0 or d < distance:
            distance = d
            index = i

    if index == len(coordinates) - 1:
        index = 0

    return coordinates[index]


def get_next_point(coordinates: List[Tuple[float, float]], point: Tuple[float, float]) -> Tuple[float, float]:
    index = coordinates.index(point)
    if index >= len(coordinates):
        return coordinates[1]
    return coordinates[index + 1]


def get_before_point(coordinates: List[Tuple[float, float]], point: Tuple[float, float]) -> Tuple[float, float]:
    index = coordinates.index(point)
    if index == 0:
        return coordinates[-2]
    return coordinates[index - 1]


def get_point_between_1_and_2(point1: Tuple[float, float], point2: Tuple[float, float]) -> Tuple[float, float]:
    increment = [point1[0], point1[1]]

    shift = 0.0001

    diff0 = point2[0] - point1[0]
    diff1 = point2[1] - point1[1]

    if abs(diff0) > abs(diff1):
        alpha = abs(diff1 / diff0)

        if diff0 >= 0:
            increment[0] += shift
        else:
            increment[0] -= shift

        if diff1 >= 0:
            increment[1] += shift * alpha
        else:
            increment[1] -= shift * alpha
    else:
        alpha = abs(diff0 / diff1)

        if diff1 >= 0:
            increment[1] += shift
        else:
            increment[1] -= shift

        if diff0 >= 0:
            increment[0] += shift * alpha
        else:
            increment[0] -= shift * alpha

    return tuple(increment)


def get_nearest_points(geom1: Polygon, geom2: Polygon) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    coord1 = geom1.exterior.coords
    coord2 = geom2.exterior.coords

    distances = dict()

    for i, c1 in enumerate(coord1):
        for j, c2 in enumerate(coord2):
            distances[(i, j)] = abs(Point(c1).distance(Point(c2)))

    index = None
    distance = None

    for key in distances.keys():
        if index is None or distance > distances[key]:
            index = key
            distance = distances[key]

    return coord1[index[0]], coord2[index[1]]


def join_coordinates_from_2_polygons(polygon1_coordinates: List[Tuple[float, float]],
                                     polygon2_coordinates: List[Tuple[float, float]],
                                     last_point_before_merge_polygon1: Tuple[float, float],
                                     first_point_after_merge_polygon1: Tuple[float, float],
                                     first_point_polygon2: Tuple[float, float],
                                     first_point_to_use_polygon2: Tuple[float, float]) -> List[Tuple[float, float]]:
    coordinates = list()
    found1 = False

    for c in polygon1_coordinates:
        if not found1 and c == last_point_before_merge_polygon1:
            coordinates.append(c)

            found1 = True

            found2 = False
            count = 0
            for c1 in polygon2_coordinates[:-1]:
                if found2:
                    coordinates.append(c1)
                elif c1 == first_point_polygon2:
                    found2 = True
                    count += 1
                    coordinates.append(first_point_to_use_polygon2)
                else:
                    count += 1

            for i in range(count):
                coordinates.append(polygon2_coordinates[i])

            coordinates.append(first_point_after_merge_polygon1)
        else:
            coordinates.append(c)

    return coordinates


def add_geom1_to_geom2(geom1: Polygon, geom2: Polygon, invert_polygon2: bool = False, invert_polygon1: bool = False):
    nearest_point_geom1, nearest_point_geom2 = get_nearest_points(geom1, geom2)

    external_coordinates1 = [c for c in geom1.exterior.coords]
    external_coordinates2 = [c for c in geom2.exterior.coords]

    next_point_geom1 = get_next_point(external_coordinates1, nearest_point_geom1) if not invert_polygon1 else \
        get_before_point(external_coordinates1, nearest_point_geom1)
    increment_point1 = get_point_between_1_and_2(nearest_point_geom1, next_point_geom1)

    next_point_geom2 = get_next_point(external_coordinates2, nearest_point_geom2) if not invert_polygon2 else \
        get_before_point(external_coordinates2, nearest_point_geom2)
    increment_point2 = get_point_between_1_and_2(nearest_point_geom2, next_point_geom2)

    if invert_polygon1:
        external_coordinates1.reverse()

    if invert_polygon2:
        external_coordinates2.reverse()

    coordinates = join_coordinates_from_2_polygons(external_coordinates1, external_coordinates2,
                                                   nearest_point_geom1, increment_point1, nearest_point_geom2,
                                                   increment_point2)

    return Polygon(coordinates)


def remove_hole(geom: Polygon) -> Polygon:
    external = get_external_polygon(geom)
    holes_geometry = get_holes_geometry(geom)
    polygon = None
    for hole in holes_geometry:
        for invert_polygon2 in [False, True]:
            for invert_polygon1 in [False, True]:
                polygon = add_geom1_to_geom2(external, hole, invert_polygon2, invert_polygon1)
                if polygon.is_valid:
                    break
            if polygon.is_valid:
                break

        external = get_external_polygon(polygon)

    return polygon


if __name__ == "__main__":
    geo = load_shape("resources/input5.json")
    print("will remove holes")
    out = remove_hole(geo)
    print(f"is valid: {out.is_valid}")
    print(f"out.interiors: {not out.interiors}")
    persist_geom(out)
    print("finished")
