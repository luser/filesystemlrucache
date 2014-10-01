#!/usr/bin/env python
#
# Copyright 2014 Mozilla Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='filesystemlrucache',
      version='0.1',
      description='Maintain a LRU cache in a filesystem directory',
      long_description=readme(),
      url='http://github.com/luser/filesystemlrucache',
      author='Ted Mielczarek',
      author_email='ted@mielczarek.org',
      license='APL2',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX :: Linux',
          'Topic :: System :: Filesystems',
      ],
      zip_safe=True,
      packages=['filesystemlrucache'],
      entry_points = {
        'console_scripts': ['filesystemlrucache=filesystemlrucache:main'],
      },
      install_requires=[
          'pyinotify',
      ]
  )
