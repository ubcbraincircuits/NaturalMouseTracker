#!/usr/bin/python3
import numpy as np
# Takes as argument a 1x30 matrix where:
# the first 10 elements code for a pickup
# The second 10 elements encode the tag
# The third 10 elements encode the reader
# Because there are so many possible conformations: its easiest to just hardcode all valid encodings.
#                |              Pickup y/n             | |       TAG       | |      READER     |
#  an example: [255,255,255,255,255,255,255,255,255,255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,]
# frame had a pick up on reader 0 of mouse 0


def parseKeyBlock(frameArray):
    """
    Takes in frame array and returns boolean indicating
    if a pick up happened on this frame
    """
    if frameArray[0][0:10].mean() in range(240, 256):
        return True
    else:
        return False


def parseCodeBlock(frameArray, start, end):
    """
    Takes in frame array, returns the integer representation of mouse tag
    encoded in block two of the array,else return nothing
    """
    if frameArray[0][start:end].mean() in range(0, 21):
        return 0  # Mouse/Reader 0

    if frameArray[0][start:end].mean() in range(70, 96):
        return 1  # Mouse/Reader 1

    if frameArray[0][start:end].mean() in range(155, 186):
        return 2  # Mouse/Reader 2

    if frameArray[0][start:end].mean() in range(240, 256):
        return 3  # Mouse/Reader 3
    return -1


def decode(frameArray):
    """
    Decodes a given 1x30 array in the described format
    returns -1 if no pick up on this frame
    else returns tuple of ints (mousetag, readernum)
​
    """
    if not parseKeyBlock(frameArray):
        return -1  # no pick up on this frame
    else:
        return (parseCodeBlock(frameArray, 10, 20), parseCodeBlock(frameArray, 20, 30))


if __name__ == "__main__":
    x = np.array([[255,255,255,255,255,255,255,255,255,255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]])
    y = np.array([[255,255,255,255,255,255,255,255,255,255, 80,80,80,80,80,80,80,80,80,80,0,0,0,0,0,0,0,0,0,0]])
    print(decode(y))
