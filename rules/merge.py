#!/usr/bin/env python3

import argparse
import os
import sys


def handle_file(path):
    '''
    Return a tuple of (header, path) for the file at path.
    If the file does not have a header, the header is the empty string.
    '''
    with open(path) as fd:
        header = fd.readline()
        if header.startswith('! '):
            return header, path
        else:
            return '', path


def merge(dest, files):
    '''
    Merge the content of all files into the file dest.

    The first line of each file is an optional section header in the form
    e.g.
       ! model =  keycodes
    Where two sections have identical headers, the second header is skipped.

    Special case are header-less files which we store with the empty string
    as header, these need to get written out first.
    '''

    def sort_basename(ftuple):
        return os.path.basename(ftuple[0])

    # sort the file list by basename
    files.sort(key=sort_basename)

    # pre-populate with the empty header so it's the first one to be written
    # out. We use section_names to keep the same order as we get the files
    # passed in (superfluous with python 3.6+ since the dict keeps the
    # insertion order anyway).
    sections = {'': []}
    section_names = ['']
    for partsfile in files:
        # files may exist in srcdir or builddir, depending whether they're
        # generated
        path = partsfile[0] if os.path.exists(partsfile[0]) else partsfile[1]

        header, path = handle_file(path)
        paths = sections.get(header, [])
        paths.append(path)
        sections[header] = paths
        if header not in section_names:
            section_names.append(header)

    for header in section_names:
        if header:
            dest.write('\n')
            dest.write(header)
        for f in sections[header]:
            with open(f) as fd:
                if header:
                    fd.readline()  # drop the header
                dest.write(fd.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser('rules file merge script')
    parser.add_argument('--dest', type=str, default=None)
    parser.add_argument('--srcdir', type=str)
    parser.add_argument('--builddir', type=str)
    parser.add_argument('files', nargs='+', type=str)
    ns = parser.parse_args()

    if ns.dest is None:
        dest = sys.stdout
    else:
        dest = ns.dest

    with dest or open(dest, 'w') as fd:
        basename = os.path.basename(sys.argv[0])
        fd.write('// DO NOT EDIT THIS FILE - IT WAS AUTOGENERATED BY {} FROM rules/*.part\n'.format(basename))
        fd.write('//\n')

        def file_tuple(f):
            '''A tuple of the given path with (builddir/f, srcdir/f)'''
            return (os.path.join(ns.builddir or '.', f), os.path.join(ns.srcdir or '.', f))

        merge(fd, [file_tuple(f) for f in ns.files])
