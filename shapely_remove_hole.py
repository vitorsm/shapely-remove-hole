import json
from typing import List, Tuple

import shapely.ops as shapely_ops
from shapely.geometry import shape, Polygon, LinearRing, Point, LineString
from shapely.geometry.base import BaseGeometry


def load_shape() -> Polygon:
    file = open("geo.json", "r")
    geo_dict = json.load(file)
    return shape(geo_dict["features"][0]["geometry"])


def persist_geom(geom: BaseGeometry):
    file = open("output.json", "w")
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


def increment_point(current_point: Tuple[float, float], next_point: Tuple[float, float],
                    only_high: bool = False) -> Tuple[float, float]:
    increment = [current_point[0], current_point[1]]

    # shift = 0.00000000000001

    shift = 0.00001
    diff0 = next_point[0] - current_point[0]
    diff1 = next_point[1] - current_point[1]

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

        if diff1 >= 0:
            increment[0] += shift * alpha
        else:
            increment[0] -= shift * alpha

    # if not only_high or diff0 > diff1:
    #     if current_point[0] > next_point[0]:
    #         increment[0] -= shift
    #     else:
    #         increment[0] += shift
    #
    # if not only_high or diff1 > diff0:
    #     if current_point[1] > next_point[1]:
    #         increment[1] -= shift
    #     else:
    #         increment[1] += shift

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


def add_geom1_to_geom2(geom1: Polygon, geom2: Polygon, force_reverse: bool = False):
    # [geom2, geom1]
    # point = shapely_ops.nearest_points(geom1, geom2)[0]

    point1, point2 = get_nearest_points(geom1, geom2)

    external_coordinates1 = [c for c in geom1.exterior.coords]
    external_coordinates2 = [c for c in geom2.exterior.coords]

    # nearest_point_geom1 = get_nearest_point_to_point(external_coordinates1, point)
    nearest_point_geom1 = point1
    next_point_geom1 = get_next_point(external_coordinates1, nearest_point_geom1)
    increment_point1 = increment_point(nearest_point_geom1, next_point_geom1)

    # nearest_point_geom2 = get_nearest_point_to_point(external_coordinates2, point)
    nearest_point_geom2 = point2
    next_point_geom2 = get_next_point(external_coordinates2, nearest_point_geom2) if not force_reverse else \
        get_before_point(external_coordinates2, nearest_point_geom2)

    # if next_point_geom2 == external_coordinates2[0]:
    #     next_point_geom2 = get_before_point(external_coordinates2, nearest_point_geom2)

    # se for foce tem que pegar o before
    # increment_next_point_geom2 = increment_point(nearest_point_geom2, next_point_geom2)
    # line1 = LineString([nearest_point_geom1, nearest_point_geom2])
    # line2_next = LineString([increment_point1, increment_next_point_geom2])
    # reverse_geom2 = line1.intersects(line2_next)
    # get_next_point(external_coordinates2, nearest_point_geom2)

    increment_next_point_geom2 = increment_point(nearest_point_geom2, next_point_geom2)
    line1 = LineString([nearest_point_geom1, increment_next_point_geom2])
    line2_next = LineString([nearest_point_geom2, increment_point1])
    reverse_geom2 = line1.intersects(line2_next)
    get_next_point(external_coordinates2, nearest_point_geom2)

    if force_reverse:
        reverse_geom2 = not reverse_geom2

    if reverse_geom2:
        print("reversed")
        external_coordinates2.reverse()
    else:
        print("not reversed")

    # if reverse_geom2 or force_reverse:
    #     print("reversed")
    #     external_coordinates2.reverse()
    # else:
    #     print("not reversed")

    next_point_geom2 = get_next_point(external_coordinates2, nearest_point_geom2)

    # increment_point2 = increment_point(nearest_point_geom2, next_point_geom2)
    increment_point2 = increment_next_point_geom2

    coordinates = list()
    found1 = False

    for c in external_coordinates1:
        if not found1 and c == nearest_point_geom1:
            coordinates.append(c)

            found1 = True

            found2 = False
            count = 0
            first_point = None
            for c1 in external_coordinates2[:-1]:
                if found2:
                    coordinates.append(c1)
                elif c1 == nearest_point_geom2:
                    found2 = True
                    first_point = c1
                    count += 1
                    coordinates.append(increment_point2)
                    # coordinates.append(c1)
                else:
                    count += 1

            for i in range(count):
                coordinates.append(external_coordinates2[i])

            # increment_point2 = increment_point(coordinates[-1], external_coordinates2[0])
            # coordinates.append(increment_point2)
            coordinates.append(increment_point1)
        else:
            coordinates.append(c)

    return Polygon(coordinates)


def remove_hole(geom: Polygon) -> Polygon:
    external = get_external_polygon(geom)
    holes_geometry = get_holes_geometry(geom)
    polygon = None
    for hole in holes_geometry:
        polygon = add_geom1_to_geom2(external, hole)
        if not polygon.is_valid:
            polygon = add_geom1_to_geom2(external, hole, True)

        external = get_external_polygon(polygon)

    return polygon


if __name__ == "__main__":
    geo = load_shape()
    out = remove_hole(geo)
    print(f"is valid: {out.is_valid}")
    persist_geom(out)
    print("finished")
