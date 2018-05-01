#!python3
import argparse

import scmFile

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('-r', '--read', action="store_const", dest="mode", const="read",
                   help="Convert SCM to one or mode CSV")
    g.add_argument('-w', '--write', action="store_const", dest="mode", const="write",
                   help="Convert CSV files back to SCM")
    parser.add_argument('-f', '--format', action="store", choices=['F', 'f', 'C', 'c'], required=True)
    parser.add_argument('file')

    args = parser.parse_args()

    if args.format.lower() == 'f':
        scm = scmFile.scmFileF()
    else:
        scm = scmFile.scmFileC()

    if args.mode == 'write':
        scm.CSV2SCM(args.file)
    else:
        scm.SCM2CSV(args.file)
