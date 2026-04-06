import os
from glob import glob

from setuptools import find_packages, setup

package_name = "cam_perception_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="CAM_PERCEPTION",
    maintainer_email="dev@example.com",
    description="ROS2 bridge for CAM_PERCEPTION",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "cam_perception_node = cam_perception_bridge.perception_node:main",
        ],
    },
)
