from setuptools import find_packages, setup

package_name = 'gesture_bridge'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Noah House',
    maintainer_email='noahhouse417@gmail.com',
    description='v1 serial bridge: reads JSON gesture lines from the camera '
                'over USB and publishes gesture_msgs/Gesture on /gesture/event.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'serial_bridge = gesture_bridge.serial_bridge:main',
        ],
    },
)
