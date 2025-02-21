from setuptools import setup, find_packages

setup(
    name="pointcloud2pgm_slicer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pytest",
        "pytest-qt",
        "PyQt5",
        "open3d",
        "pyvista",
        "pyvistaqt",
        "matplotlib"
    ],
)
