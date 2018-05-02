import scmFile
import argparse


def compareA(rows_old: dict, rows_new: dict) -> None:
    used_numbers = list(range(1, 101))

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

                    used_numbers.remove(int(row['Number']))

    # Place unassigned channels to available numbers
    for row in rows_new:
        if row['Number'] > 1000:
            row['Number'] = used_numbers.pop(0)


def compareD(rows_old: dict, rows_new: dict) -> None:
    used_numbers = list(range(1, 101))

    # TODO: how to uniq. identify digi channels? Only by name?
    # # In order to avoid duplicate numbers, renumber the channels in new list
    # for i, row in enumerate(rows_new):
    #     row['Number'] = 1000 + i
    #
    # for row in rows_old:
    #     if row['Used'] == 1:
    #         for row2 in rows_new:
    #             # Two analog channels match if they have the same frequency
    #             if row2['Frequency'] == row['Frequency']:
    #                 for k in row2.keys():
    #                     if k == 'Name' and not row[k]:
    #                         continue
    #                     row2[k] = row[k]
    #
    #                 used_numbers.remove(int(row['Number']))
    #
    # # Place unassigned channels to available numbers
    # for row in rows_new:
    #     if row['Number'] > 1000:
    #         row['Number'] = used_numbers.pop(0)


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

    scm[0].CSV2SCM(args.file[0])
    scm[1].SCM2CSV(args.file[1])

    pass


if __name__ == "__main__":
    main()
