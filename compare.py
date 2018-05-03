import argparse
import os
import scmFile


def compareA(rows_old: dict, rows_new: dict) -> None:
    free_numbers = list(range(1, 101))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, row in enumerate(rows_new):
        row['Number'] = 1000 + i

    for row in rows_old:
        if row['Used'] == 1:
            for row2 in rows_new:
                # Two analog channels match if they have the same frequency
                if row2['Frequency'] == row['Frequency']:
                    for k in row2.keys():
                        if k == 'Name' and not row[k]:
                            continue
                        row2[k] = row[k]

                    free_numbers.remove(int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] > 1000:
            row['Number'] = free_numbers.pop(0)


def compareD(rows_old: dict, rows_new: dict) -> None:
    used_numbers = list(range(1, 101))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, row in enumerate(rows_new):
        row['Number'] = 1000 + i

    for row in rows_old:
        if row['Number'] != 1000:
            for row2 in rows_new:
                # Two digital channels match if they have the same name
                if row2['Name'] == row['Name']:
                    for k in row2.keys():
                        row2[k] = row[k]

                    used_numbers.remove(int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] > 1000:
            row['Number'] = used_numbers.pop(0)


def main():
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-f', '--format', action="store", choices=['F', 'f', 'C', 'c'], required=True)
    parser.add_argument('file', nargs=2)

    args = parser.parse_args()

    if args.format.lower() == 'f':
        scm = [scmFile.scmFileF(), scmFile.scmFileF()]
    else:
        scm = [scmFile.scmFileC(), scmFile.scmFileC()]

    os.makedirs("old", exist_ok=True)
    os.makedirs("new", exist_ok=True)

    scm[0].readSCM(args.file[0], "old")
    scm[1].readSCM(args.file[1], "new")

    for fmt in ('A', 'D'):
        for src in ('Air', 'Cable'):
            method = compareA if fmt == 'A' else compareD
            fname = 'map-{0}{1}'.format(src, fmt)
            method.__call__(scm[0].rows[fname], scm[0].rows[fname])
            scm[1].writeMap(os.path.join("new",  fname))

    scm[1].writeSCM(args.file[1], "new")


if __name__ == "__main__":
    main()
