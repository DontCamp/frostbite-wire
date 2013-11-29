from setuptools import setup

setup(
    test_suite='tests',
    tests_require=['unittest2'],
    setup_requires=['pbr'],
    pbr=True,
)
