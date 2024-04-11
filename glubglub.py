from svgelements import *
from sys import argv
from xml.etree.ElementTree import ElementTree, Element, fromstring, register_namespace

def is_outline(element: Shape):
    if not element.fill:
        return False

    r, g, b = element.fill.red, element.fill.green, element.fill.blue

    return (r == 0 or (r and r <= 26)) and (g == 0 or (g and g <= 26)) and (b == 0 or (b <= 26))

def is_clip_outline(element: Shape):
    if not isinstance(element, Path):
        return False
    
    if element.count_subpaths() < 2:
        return False
    
    return is_outline(element)

def is_touching_island(island: Group | Shape, element: Group | Shape):
    island_x1, island_y1, island_x2, island_y2 = island.bbox()
    element_x1, element_y1, element_x2, element_y2 = element.bbox()

    return element_x1 <= island_x2 and element_x2 >= island_x1 and element_y1 <= island_y2 and element_y2 >= island_y1


def is_inside_island(island: Group | Shape, element: Group | Shape):
    island_x1, island_y1, island_x2, island_y2 = island.bbox()
    element_x1, element_y1, element_x2, element_y2 = element.bbox()

    return element_x1 >= island_x1 and element_x2 <= island_x2 and element_y1 >= island_y1 and element_y2 <= island_y2


def clip_to_outlines(input_island: Group, input_island_index: int):
    output_island = Group()

    elements: list[Shape] = list(input_island)
    index = len(elements) - 1

    clip_paths: list[Path] = []

    while index >= 0:
        element: Shape | Path = elements[index]

        if is_clip_outline(element):
            index -= 1

            clip_path = Path(element.subpath(0))
            clip_path.fill = Color("red")
            clip_path.stroke = Color("transparent")

            clip_path.values[SVG_ATTR_ID] = f"island{input_island_index}-clip{len(clip_paths) + 1}"
            fill_element = Path(element.subpath(0))

            clip_paths.append(clip_path)

            clipped_group = Group()
            clipped_group.values[SVG_ATTR_ID] = f"island{input_island_index}-group{len(clip_paths) + 1}"
            clipped_group.append(fill_element)

            while index >= 0:
                clipped_element = elements[index]

                if not is_clip_outline(clipped_element) and is_inside_island(fill_element, clipped_element):
                    clipped_group.insert(1, clipped_element)
                else:
                    break

                index -= 1

            if len(clipped_group) >= 2:
                fill_element.fill = clipped_group[1].fill
            else:
                fill_element.fill = Color("red")
            
            clipped_group.values[SVG_ATTR_CLIP_PATH] = f"url(#{clip_path.values.get(SVG_ATTR_ID)})"
            output_island.insert(0, clipped_group)
        else:
            output_island.insert(0, element)
            index -= 1


    return output_island, clip_paths

def get_islands(elements: list[Shape]) -> list[Group]:
    islands: list[Group] = []

    remaining = list(elements)
    while len(remaining) > 0:
        island = Group()
        island.append(remaining.pop(0))

        pending = True
        while pending:

            pending = False
            for index in range(len(remaining)):
                element = remaining[index]

                if is_touching_island(island, element):
                    island.append(remaining.pop(index))
                    pending = True
                    break

        islands.append(island)
    
    return islands

def add_clip_paths(filename: str, clip_paths: list[Path]):
    register_namespace("", "http://www.w3.org/2000/svg")

    svg = ElementTree(file=filename)

    defs = svg.find("./{http://www.w3.org/2000/svg}defs")
    if defs == None:
        defs = Element("{http://www.w3.org/2000/svg}defs")
        svg.getroot().insert(0, defs)
    
    for clip_path in clip_paths:
        clip_path_element: Element = Element("{http://www.w3.org/2000/svg}clipPath", attrib={"clip-rule":"nonzero"})
        clip_path_element.attrib[SVG_ATTR_ID] = clip_path.values.get(SVG_ATTR_ID)

        path_element = fromstring(clip_path.string_xml())
        if SVG_ATTR_ID in path_element.attrib:
            path_element.attrib.pop(SVG_ATTR_ID)

        clip_path_element.append(path_element)
        defs.append(clip_path_element)

    svg.write(filename)

def main(inputFilename, outputFilename):
    inputSvg: SVG = SVG.parse(inputFilename)
    inputElements: list[Shape] = []
    
    for element in inputSvg.elements():
        if isinstance(element, Shape) and not ((element.fill and element.fill.alpha and element.fill.alpha > 0) or (element.stroke_width and element.stroke_width > 0)):
            continue

        if isinstance(element, Polygon):
            inputElements.append(Path(element))
        elif isinstance(element, Path):
            inputElements.append(element)

    input_islands = get_islands(inputElements)

    output_islands: list[Group] = []
    output_clip_paths: list[Path] = []
    input_island_index = 0
    for input_island in input_islands:
        input_island_index += 1

        output_island, output_island_clip_paths = clip_to_outlines(input_island, input_island_index)
        output_island.values[SVG_ATTR_ID] = f"island{input_island_index}"
        output_islands.append(output_island)
        output_clip_paths.extend(output_island_clip_paths)

    outputSvg = SVG(width=inputSvg.width, height=inputSvg.height)
    outputSvg.viewbox = inputSvg.viewbox
    outputSvg.extend(output_islands)

    outputSvg.write_xml(outputFilename)
    add_clip_paths(outputFilename, output_clip_paths)

if len(argv) > 2:
    main(argv[1], argv[2])