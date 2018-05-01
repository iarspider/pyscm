import argparse

import scmFile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", "-f", help="Source file format", dest="from_type", required=True,
                        choices=['F', 'f', 'C', 'c'])
    parser.add_argument("--to", "-t", help="Target file format", dest="to_type", required=True,
                        choices=['F', 'f', 'C', 'c'])
    parser.add_argument("infile", help="Source file name", required=True)
    parser.add_argument("outfile", help="Target file name", required=True)

    args = parser.parse_args()

    if args.from_type.lower() == 'f':
        inFile = scmFile.scmFileF()
    else:
        inFile = scmFile.scmFileC()

    if args.to_type.lower() == 'f':
        outFile = scmFile.scmFileF()
    else:
        outFile = scmFile.scmFileC()


# TODO: Finish code

if __name__ == "__main__":
    main()
