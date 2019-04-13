from setuptools import setup, find_packages


setup(
    name='sinzlab_tools',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Fabric'
    ],
    entry_points='''
        [console_scripts]
        sinzlab-tools=sinzlab_tools.main:cli
    ''',
)
