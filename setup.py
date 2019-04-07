from setuptools import setup


setup(
    name='sinzlab-tools',
    version='0.o.1',
    py_modules=['sinzlab_tools'],
    install_requires=[
        'Click',
        'Fabric'
    ],
    entry_points='''
        [console_scripts]
        sinzlab_tools=sinzlab_tools:cli
    ''',
)
