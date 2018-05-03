import argparse
import os, shutil
import scmFile

from collections import deque


def compareA(rows_old: dict, rows_new: dict) -> None:
    free_numbers = deque(range(1, 1000))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, row in enumerate(rows_new):
        row['Number'] = 10000 + i

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
                    print("Matched channel, set to number", int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] > 10000:
            try:
                row['Number'] = free_numbers.popleft()
            except IndexError as e:
                print("Failed to reassign channel!", e)
            else:
                print("Assigned channel {Name} ({Frequency}) to number {Number}".format(**row))


def compareD(rows_old: dict, rows_new: dict) -> None:
    used_numbers = deque(range(1, 1000))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, row in enumerate(rows_new):
        row['Number'] = 10000 + i

    for row in rows_old:
        if row['Number'] != 10000:
            for row2 in rows_new:
                # Two digital channels match if they have the same name
                if row2['Name'] == row['Name']:
                    for k in row2.keys():
                        row2[k] = row[k]

                    used_numbers.remove(int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] > 10000:
            try:
                row['Number'] = used_numbers.popleft()
            except IndexError as e:
                print("Failed to reassign channel", e)
            else:
                print("Assigned channel {Name} to number {Number}".format(**row))


def main():
    parser = argparse.ArgumentParser()
    # g = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-f', '--format', action="store", choices=['F', 'f', 'C', 'c'], required=True)
    parser.add_argument('old')
    parser.add_argument('new')

    args = parser.parse_args()

    if args.format.lower() == 'f':
        scm = [scmFile.scmFileF(), scmFile.scmFileF()]
    else:
        scm = [scmFile.scmFileC(), scmFile.scmFileC()]

    os.makedirs("old", exist_ok=True)
    os.makedirs("new", exist_ok=True)

    scm[0].readSCM(args.old, "old")
    scm[1].readSCM(args.new, "new")

    for fmt in ('A', 'D'):
        for src in ('Air', 'Cable'):
            method = compareA if fmt == 'A' else compareD
            fname = 'map-{0}{1}'.format(src, fmt)
            scm[1].writeCSV(os.path.join("new", fname + '.csv'))
            shutil.move(os.path.join("new", fname + '.csv'), os.path.join("new", fname + '_old.csv'))
            method.__call__(scm[0].rows[fname], scm[0].rows[fname])
            # scm[1].writeMap(os.path.join("new",  fname))
            scm[1].writeCSV(os.path.join("new", fname + '.csv'))

    # scm[1].writeSCM(args.file[1], "new")


if __name__ == "__main__":
    main()
