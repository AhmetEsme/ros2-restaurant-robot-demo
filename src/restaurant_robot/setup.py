from setuptools import find_packages, setup

package_name = 'restaurant_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/params.yaml']),
        ('share/' + package_name + '/launch', ['launch/restaurant.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ahmet',
    maintainer_email='280829604+AhmetEsme@users.noreply.github.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'robot_controller = restaurant_robot.robot_controller:main',
            'table_status_publisher = restaurant_robot.table_status_publisher:main',
            'order_manager = restaurant_robot.order_manager:main',
            'monitor = restaurant_robot.monitor:main',
            'demo = restaurant_robot.demo_runner:main',
        ],
    },
)
