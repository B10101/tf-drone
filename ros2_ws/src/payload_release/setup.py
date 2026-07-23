import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'payload_release'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='drone project',
    maintainer_email='againdnf@gmail.com',
    description='Servo-actuated payload release, triggered from a FlySky RC switch via MAVROS or a software service.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'release_node = payload_release.release_node:main',
        ],
    },
)
