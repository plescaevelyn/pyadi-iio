from setuptools import find_packages, setup

package_name = "adalm_lsmspg_servo_demo"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pyadi-iio"],
    zip_safe=True,
    maintainer="Your Name",
    maintainer_email="your_email@example.com",
    description="ROS2 Hello World demo with ADALM-LSMSPG and IIO",
    license="ADIBSD",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "servo_commander = adalm_lsmspg_servo_demo.servo_commander:main",
            "servo_feedback = adalm_lsmspg_servo_demo.servo_feedback:main",
        ],
    },
)
