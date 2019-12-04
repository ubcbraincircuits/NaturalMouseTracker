import setuptools
from shutil import copy2
from os import path

here = path.abspath(path.dirname(__file__))

darknetPath = input("Please enter the full path to your darknet installation.\
    On Windows, this will look similar to C:/Users/<user>/.../darknet/ .")

copy2(darknetPath + "/build/darknet/x64/pthreadGC2.dll", "./naturalmousetracker/data/")
copy2(darknetPath + "/build/darknet/x64/pthreadVC2.dll", "./naturalmousetracker/data/")
copy2(darknetPath + "/build/darknet/x64/yolo_cpp_dll.dll", "./naturalmousetracker/data/")
copy2(darknetPath + "/build/darknet/x64/pthreadGC2.dll", "./naturalmousetracker/detection_utils/")
copy2(darknetPath + "/build/darknet/x64/pthreadVC2.dll", "./naturalmousetracker/detection_utils/")
copy2(darknetPath + "/build/darknet/x64/yolo_cpp_dll.dll", "./naturalmousetracker/detection_utils/")

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
print(setuptools.find_packages())
setuptools.setup(
    name="naturalmousetracker-Judge24601", # Replace with your own username
    version="0.1.0",
    author="Braeden Jury",
    author_email="braedenjury@gmail.com",
    description="Mouse Tracking and Pose Estimation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Judge24601/MouseTrackingSystem",
    packages=setuptools.find_packages(),
    package_data={'naturalmousetracker': [
        "*.dll",
        "*.weights",
        "data/*"
    ], 'naturalmousetracker.detection_utils': ['*.dll']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
