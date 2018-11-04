# SPDX-License-Identifier: GPL-3.0+

from setuptools import setup, find_packages

requirements = []
with open('requirements.txt', 'r') as f:
    requirements = f.readlines()

setup(
    name='adreset',
    version='0.1',
    description='The ADReset API',
    author='Matt Prahl',
    author_email='mprahl@users.noreply.github.com',
    license='GPLv3+',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=requirements,
)
