from svgelements import *
from sys import argv

def main(inputFilename, outputFilename, remappedColors: list[str]):
    inputFile = ""
    with open(inputFilename, "r") as file:
        inputFile = file.read()

    colors = {}
    for color in remappedColors:
        c = color.split("=")

        if len(c) == 2:
            inputFile = inputFile.replace(c[0].upper(), c[1])
            inputFile = inputFile.replace(c[0].lower(), c[1])
            
    with open(outputFilename, "w") as file:
        file.write(inputFile)

if len(argv) > 2:
    main(argv[1], argv[2], argv[3:])