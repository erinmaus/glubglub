from svgelements import *
from sys import argv
from math import floor, sqrt
import numpy as np

def collect_parents(parent: SVGElement):
    for child in parent:
        if isinstance(child, SVGElement):
            child.parent = parent
            collect_parents(child)

def get_clip_paths(element: SVGElement, clip_paths: list[SVGElement]):
    if hasattr(element, "clip_path") and not (element.clip_path in clip_paths):
        clip_paths.append(element.clip_path)

    if hasattr(element, "parent"):
        get_clip_paths(element.parent, clip_paths)

    return clip_paths

def _try_remove_point(points: list[tuple[float, float]], distance: float):
    for point in points:
        other_points = list(filter(lambda p: np.linalg.norm(np.array(p) - np.array(point)) > distance or p == point, points))

        if len(other_points) < len(points):
            print(len(points), len(points) - len(other_points))

            points.clear()
            points.extend(other_points)

            return True
    
    return False

def remove_close_points(points: list[tuple[float, float]], distance=1):    
    result = list(points)
    while _try_remove_point(result, distance):
        pass

    return result

def render_path(element: Polygon | Path):
    if isinstance(element, Polygon):
        element = Path(element)

    subpaths: list[list[tuple[int, int]]] = []
    if isinstance(element, Path):
        element.approximate_arcs_with_cubics()
        
        for i in range(element.count_subpaths()):
            subpath = element.subpath(i)

            points: list[tuple[int, int]] = []
            for segment in subpath:
                if isinstance(segment, Move):
                    point = np.array([segment.end.x, segment.end.y])
                    point = np.floor(point * 100) / 100
                    if len(points) == 0 or not np.any(np.all(point == points, axis=1)):
                        points.append((segment.end.x, segment.end.y))
                elif isinstance(segment, Line):
                    point = np.array([segment.end.x, segment.end.y])
                    point = np.floor(point * 100) / 100
                    if not np.any(np.all(point == points, axis=1)):
                        points.append((segment.end.x, segment.end.y))
                elif isinstance(segment, QuadraticBezier) or isinstance(segment, CubicBezier):
                    length = segment.length()
                    num_points = max(floor(length / 10), 2)

                    for i in range(num_points):
                        delta = i / (num_points - 1)
                        point = segment.npoint([delta])[0]
                        point = np.floor(point * 100) / 100

                        if not np.any(np.all(point == points, axis=1)):
                            points.append((point[0], point[1]))
                else:
                    continue

            points = remove_close_points(points)

            if len(points) >= 3:
                subpaths.append(points)
    
    return subpaths

def element_to_lua(element: Polygon | Path, is_clip = False, id: str | None = None):
    result = "\t\t{\n"

    if SVG_ATTR_ID in element.values:
        result += f"\t\t\tid = \"{element.values[SVG_ATTR_ID]}\",\n"
    elif id != None:
        result += f"\t\t\tid = \"{id}\",\n"

    if hasattr(element, "fill") and element.fill and not is_clip:
        result += f"\t\t\tfill = \"{element.fill}\",\n"

    clip_paths = get_clip_paths(element, [])
    if clip_paths and len(clip_paths) >= 1 and not is_clip:
        result += "\t\t\tclip = { "
        for clip_path in clip_paths:
            if clip_path.values[SVG_ATTR_ID]:
                result += f"\"{clip_path.id}\", "
        result += "},\n"

    subpaths = render_path(element)
    for subpath in subpaths:
        result += "\t\t\t{\n"
        for point in subpath:
            result += f"\t\t\t\t{point[0]:.02f}, {point[1]:.02f},\n"
        result += "\t\t\t},\n"

    result += "\t\t},\n"
    
    return result

def main(inputFilename, outputFilename):
    inputSvg: SVG = SVG.parse(inputFilename)

    collect_parents(inputSvg)

    result = "{\n"
    result += f"\twidth = {inputSvg.width:.0f},\n"
    result += f"\theight = {inputSvg.height:.0f},\n"
    result += "\tpaths =\n"
    result += "\t{\n"

    clip_paths_by_id: dict[SVGElement] = {}
    for element in inputSvg.elements():
        if isinstance(element, Polygon) or isinstance(element, Path):
            clip_paths = get_clip_paths(element, [])
            for clip_path in clip_paths:
                clip_path_id = clip_path.values[SVG_ATTR_ID]
                if not (clip_path_id in clip_paths_by_id):
                    clip_paths_by_id[clip_path_id] = clip_path
            result += element_to_lua(element)

    result += "\t},\n"
    result += "\tclips =\n"
    result += "\t{\n"
    for clip_path_id in clip_paths_by_id:
        result += element_to_lua(clip_paths_by_id[clip_path_id][0], True, clip_path_id)
    result += "\t},\n"
    result += "}\n"

    with open(outputFilename, "w") as file:
        file.write(result)

if len(argv) > 2:
    main(argv[1], argv[2])