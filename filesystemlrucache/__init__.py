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

__all__ = [
    'CacheMonitor',
]

import argparse
import os
import pyinotify
import sys
from collections import OrderedDict


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, monitor, verbosity=0):
        pyinotify.ProcessEvent.__init__(self)
        self.monitor = monitor
        self.verbosity = verbosity

    def process_IN_DELETE(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('D')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'D  ', event.pathname
            self.monitor._remove_cached(event.pathname)

    def process_IN_CREATE(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('C')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'C  ', event.pathname
            self.monitor._update_cache(event.pathname)

    def process_IN_MOVED_FROM(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('M')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'M> ', event.pathname
            self.monitor._remove_cached(event.pathname)

    def process_IN_MOVED_TO(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('M')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'M< ', event.pathname
            self.monitor._update_cache(event.pathname)

    def process_IN_OPEN(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('O')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'O  ', event.pathname
            self.monitor._update_cache(event.pathname)

    def process_IN_MODIFY(self, event):
        if not event.dir:
            if self.verbosity == 1:
                sys.stdout.write('M')
                sys.stdout.flush()
            elif self.verbosity == 2:
                print 'M  ', event.pathname
            self.monitor._update_cache(event.pathname, update_size=True)


class CacheMonitor:
    def __init__(self, directory, size, verbosity=0):
        self.directory = os.path.abspath(directory)
        self.max_size = size
        self.verbosity = verbosity
        # Cache state
        self.total_size = 0
        self._lru = OrderedDict()
        # pyinotify bits
        self._wm = pyinotify.WatchManager()
        self._handler = EventHandler(self, verbosity=verbosity)
        self._notifier = pyinotify.Notifier(self._wm, self._handler)
        mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE \
            | pyinotify.IN_OPEN | pyinotify.IN_MOVED_FROM \
            | pyinotify.IN_MOVED_TO | pyinotify.IN_MODIFY
        self._wdd = self._wm.add_watch(
            self.directory,
            mask,
            rec=True,
            auto_add=True
        )
        # Load existing files into the cache.
        self._get_existing_files(self.directory)

    @property
    def num_files(self):
        return len(self._lru)

    def run_forever(self):
        self._notifier.loop()

    def _rm_empty_dirs(self, path):
        '''
        Attempt to remove any empty directories that are parents of path
        and children of self.directory.
        '''
        path = os.path.dirname(path)
        while not os.path.samefile(path, self.directory):
            if not os.listdir(path):
                os.rmdir(path)
            path = os.path.dirname(path)

    def _update_cache(self, path, update_size=False):
        if path in self._lru:
            size = self._lru.pop(path)
            if update_size:
                self.total_size -= size
        else:
            update_size = True

        if update_size:
            size = os.stat(path).st_size
            self.total_size += size
            # If we're out of space, remove items from the cache until
            # we fit again.
            while self.total_size > self.max_size and self._lru:
                rm_path, rm_size = self._lru.popitem(last=False)
                self.total_size -= rm_size
                os.unlink(rm_path)
                self._rm_empty_dirs(rm_path)
                if self.verbosity >= 2:
                    print 'RM ', rm_path
        self._lru[path] = size

    def _remove_cached(self, path):
        # We might have already removed this file in _update_cache.
        if path in self._lru:
            size = self._lru.pop(path)
            self.total_size -= size

    def _get_existing_files(self, path):
        for base, dirs, files in os.walk(path):
            for f in files:
                f = os.path.join(base, f)
                self._update_cache(f)


def parse_size(size):
    '''
    Parse a size argument of the form \d+[kMG] that represents a size in
    bytes, with the suffixes representing kilobytes, megabytes or gigabytes
    respectively.
    '''
    suffixes = {
        'k': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3,
    }
    if not isinstance(size, basestring) or not size:
        raise ValueError('Bad size value: "%s"' % size)

    if size[-1].isdigit():
        return int(size)

    if size[-1] not in suffixes:
        raise ValueError('Unknown size suffix: "%s"' % size[-1])

    return int(size[:-1]) * suffixes[size[-1]]


def main():
    parser = argparse.ArgumentParser(description='Monitor a directory tree ' +
                                     'with inotify and maintain a maximum ' +
                                     ' size of the total contents.')
    parser.add_argument('directory', metavar='DIR', type=str, action='store',
                        help='the directory to monitor')
    parser.add_argument('size', action='store', type=parse_size,
                        help='maximum size of the directory contents in bytes')
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--shutdown-summary', action='store_true',
                        help='print a summary on shutdown')
    args = parser.parse_args()
    monitor = CacheMonitor(args.directory, args.size,
                           verbosity=args.verbose)
    monitor.run_forever()
    if args.verbose == 1:
        print
    if args.shutdown_summary:
        print "Files: %d" % monitor.num_files
        print "Total size: %d bytes" % monitor.total_size

if __name__ == '__main__':
    main()
