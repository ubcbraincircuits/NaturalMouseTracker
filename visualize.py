import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
fileName = "test.txt"

mice = {}
file = open(fileName)
file.seek(0)
for line in file:
    ln = line.split(";")
    mouse = mice.get(ln[1], None)
    if mouse is None:
        mice.update({ln[1]: [{"position": [item for item in ln[2].strip('()\n').split(',')], "time": float(ln[0])}]})
    else:
        mice[ln[1]].append({"position": [item for item in ln[2].strip('()\n').split(',')], "time": float(ln[0])})
fig = plt.figure()
img = mpimg.imread("ref.jpg")
plt.imshow(img)
plt.axis((0, 640, 0, 480))
for mouse in mice.values():
    positions = list(map(lambda x: x["position"], sorted(mouse, key=lambda x: x["time"])))
    x = list(map(lambda x: int(x[0]), positions))
    y = list(map(lambda x: int(x[1]), positions))
    print(positions)
    print(y)
    plt.plot(x, y)
plt.show()
