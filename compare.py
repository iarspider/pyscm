import argparse
import os
import shutil
from collections import deque

import scmFile


def compareA(rows_old: dict, rows_new: dict) -> None:
    free_numbers = deque(range(1, 10000))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, row in enumerate(rows_new):
        row['Number'] = -i

    for row in rows_old:
        if row['Used'] == 1:
            for row2 in rows_new:
                # Two analog channels match if they have the same frequency
                if row2['Frequency'] == row['Frequency']:
                    print("Match found: ", row['Number'], row['Frequency'])
                    for k in row2.keys():
                        if k == 'Name' and not row[k]:
                            continue
                        row2[k] = row[k]

                    free_numbers.remove(int(row['Number']))
                    print("Matched channel, set to number", int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] < 0:
            try:
                row['Number'] = free_numbers.popleft()
            except IndexError as e:
                print("Failed to reassign channel!", e)
            else:
                if row['Name']:
                    print("Assigned channel {Name} ({Frequency}) to number {Number}".format(**row))


def compareD(rows_old: dict, rows_new: dict) -> None:
    free_numbers = deque(range(1, 10000))

    # In order to avoid duplicate numbers, renumber the channels in new list
    for i, new in enumerate(rows_new):
        new['Number'] = -i

    for old in rows_old:
        if old['Number'] != 0:
            for new in rows_new:
                # Two digital channels match if they have the same name
                if new['Number'] != 0 and new['Name'] == old['Name']:
                    print("Matched channel", old['Name'], "@", old['Number'])
                    # print(old)
                    for k in new.keys():
                        new[k] = old[k]

                    try:
                        free_numbers.remove(int(old['Number']))
                    except ValueError:
                        print("Failed to make channel number as used:", int(old['Number']))
                        new['Number'] = -1
                        pass
                    except Exception as e:
                        print(e)

    # Place unassigned channels to available numbers
    for new in rows_new:
        if new['Number'] < 0:
            try:
                new['Number'] = free_numbers.popleft()
            except IndexError as e:
                print("Failed to reassign channel", e)
            else:
                if new['Name']:
                    print("Assigned channel {Name} to number {Number}".format(**new))


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

    print("Reading reference file")
    scm[0].readSCM(args.old, "old")
    print("Reading target file")
    scm[1].readSCM(args.new, "new")

    for fmt in ('A', 'D'):
        for src in ('Air', 'Cable'):
            method = compareA if fmt == 'A' else compareD
            fname = 'map-{0}{1}'.format(src, fmt)
            print("Comparing file {0}".format(fname))
            scm[0].writeCSV(os.path.join("old", fname + '.csv'))
            scm[1].writeCSV(os.path.join("new", fname + '.csv'))
            shutil.move(os.path.join("new", fname + '.csv'), os.path.join("new", fname + '_orig.csv'))
            method(scm[0].rows[fname], scm[1].rows[fname])
            scm[1].writeCSV(os.path.join("new", fname + '.csv'))
            scm[1].writeMap(os.path.join("new",  fname))

    # scm[1].writeSCM(args.file[1], "new")


if __name__ == "__main__":
    main()
