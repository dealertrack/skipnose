from __future__ import unicode_literals, print_function
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), 'rb').read().decode('utf-8')


setup(
    name='dtnose',
    version='0.1.0',
    description='conditionally run selective nosetests',
    long_description=read('README.rst'),
    url='http://10.134.8.70/E003134/dt-nose',
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=[
        'setuptools',
    ],
    entry_points={
        'nose.plugins.0.10': [
            'NOSETESTS_DTNOSE = dtnose:DtNose'
        ]
    },
    keywords=' '.join([
        'test',
        'nosetests',
        'nose',
        'nosetest',
    ]),
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
    ],
    license='MIT',
)
