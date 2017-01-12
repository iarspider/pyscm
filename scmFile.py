import codecs
import csv
import os
import struct
import sys
import zipfile
from collections import OrderedDict


# Ripoff of Python's own DictReader, returns OrderedDict instead of regulat dict
class OrderedDictReader(csv.DictReader):
    def __next__(self):
        if self.line_num == 0:
            # noinspection PyStatementEffect
            # Used only for its side effect.
            self.fieldnames
        row = next(self.reader)
        self.line_num = self.reader.line_num

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while not row:
            row = next(self.reader)
        d = OrderedDict(zip(self.fieldnames, row))
        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]
        elif lf > lr:
            for key in self.fieldnames[lr:]:
                d[key] = self.restval
        return d


class OrderedDictWriter(csv.DictWriter):
    def writeheader(self):
        header = OrderedDict(zip(self.fieldnames, self.fieldnames))
        self.writerow(header)


class scmFile(object):
    def __init__(self, formatA, formatD):
        self.struct = {'A': '<' + "".join(x[1] for x in formatA),
                       'D': '<' + "".join(x[1] for x in formatD)}
        self.fieldNames = {'A': [x[0] for x in formatA],
                           'D': [x[0] for x in formatD]}
        self.blockSize = {'A': struct.calcsize(self.struct['A']),
                          'D': struct.calcsize(self.struct['D'])}
        self.parse = {'A': self.parseA, 'D': self.parseD}
        self.pack = {'A': self.packA, 'D': self.packD}

    @staticmethod
    def bytes2utf16(data):
        try:
            result = data.rstrip(b'\x00').decode('utf_16_be', errors="ignore")
        except ValueError:
            print("Warning: failed to decode Name field!")
            result = ""

        return result

    def parseA(self, data: bytes) -> OrderedDict:
        valz = struct.unpack(self.struct['A'], data)
        chan = OrderedDict(zip(self.fieldNames['A'], valz))

        if chan['Length'] == 0:
            chan['Name'] = ''
        else:
            chan['Name'] = self.bytes2utf16(chan['Name'])

        return chan

    def packA(self, chan: OrderedDict) -> bytes:
        chan['Name'] = chan['Name'].ljust(12, '\x00').encode("utf_16_be")

        if len(chan['Name']) == 0:
            chan['Length'] = 0
        else:
            chan['Length'] = 12  # length - always 12?

        chan['CRC'] = '0'

        for i, x in enumerate(chan):
            try:
                chan[i] = int(x)
            except ValueError:
                chan[i] = x

        chan['Freq'] = float(chan['Freq'])

        data = struct.pack(self.struct['A'], *chan.values())

        # Calculate CRC
        crc = sum(data) & 0xFF
        chan[19] = crc
        data = struct.pack(self.struct['A'], *chan.values())
        return data

    def parseD(self, data: bytes) -> OrderedDict:
        valz = struct.unpack(self.struct['D'], data)
        chan = OrderedDict(zip(self.fieldNames['D'], valz))

        chan['Name'] = self.bytes2utf16(chan['Name'])
        chan['Short'] = self.bytes2utf16(chan['Short'])

        if chan['Name'] != "":
            for k, v in chan.items():
                print(k, ' = "', v, '"')

        return chan

    def packD(self, chan: OrderedDict) -> bytes:
        chan['Name'] = chan['Name'].ljust(200, '\x00').encode("utf_16_be")
        chan['Short'] = chan['Short'].ljust(18, '\x00').encode("utf_16_be")

        chan['Unknown50'] = '\x00' * 6  # Hax!
        chan['CRC'] = 0

        for i, x in enumerate(chan):
            try:
                chan[i] = int(x)
            except ValueError:
                chan[i] = x

        data = struct.pack(self.struct['D'], *chan)

        # Calculate CRC
        crc = sum(data) & 0xFF
        chan['CRC'] = crc
        data = struct.pack(self.struct['D'], *chan)
        return data

    def read(self, fileName: str, key: str) -> None:
        ifile = open(fileName, "rb")
        # print "Decoding file {0}...".format(fileName),
        ofile = codecs.open(fileName + '.csv', 'w', 'utf8')
        w = OrderedDictWriter(ofile, fieldnames=self.fieldNames[key])
        w.writeheader()

        while True:
            data = ifile.read(self.blockSize[key])
            if len(data) != self.blockSize[key]:
                # print "done!"
                break
            rowDict = self.parse[key](data)
            w.writerow(rowDict)

        ofile.close()

    def write(self, ofilename: str, key: str) -> None:
        # print "Packing {0}...".format(ofilename),
        ofile = open(ofilename, "wb")
        ifile = open(ofilename + '.csv', "r")
        r = OrderedDictReader(ifile)
        for row in r:
            ofile.write(self.pack[key](row))

        ofile.close()

    def readA(self, fileName: str) -> None:
        self.read(fileName, 'A')

    def writeA(self, fileName: str) -> None:
        self.write(fileName, 'A')

    def readD(self, fileName: str) -> None:
        self.read(fileName, 'D')

    def writeD(self, fileName: str) -> None:
        self.write(fileName, 'D')

    def readSCM(self, zName):
        if zName == "":
            print("ERROR: No scm file(s) found!")
            sys.exit(0)

        dirName = zName.rsplit('.', 1)[0]
        os.makedirs(dirName, exist_ok=True)

        print("Unpacking files from {0}:".format(zName))

        zFile = zipfile.ZipFile(zName, "r")
        for fName in ("map-AirA", "map-AirD", "map-CableA", "map-CableD"):
            print("\t" + fName + "...", end='')
            try:
                zFile.extract(fName, path=dirName)
            except KeyError as e:
                print(e)
                print("skipped!")
            else:
                # data = zFile.read(fName)
                # ifile = StringIO(data)
                if fName.endswith('A'):
                    self.readA(os.path.join(dirName, fName))

                if fName.endswith('D'):
                    self.readD(os.path.join(dirName, fName))
                print("done!")

        print("All done!")
        zFile.close()

    def writeSCM(self, zName):
        if zName == "":
            print("ERROR: No scm file(s) found!")
            sys.exit(0)

        dirName = zName.rsplit('.', 1)[0]
        os.makedirs(dirName, exist_ok=True)

        print("Unpacking all files from {0}...".format(zName), end="")
        zFile = zipfile.ZipFile(zName, "r")
        zFile.extractall(dirName)
        zFile.close()
        print("done!")

        zFile = zipfile.ZipFile(zName, "w", zipfile.ZIP_DEFLATED)

        print("Packing modified files:")
        for fName in ("map-AirA", "map-AirD", "map-CableA", "map-CableD"):
            print("\t" + fName + "...", end="")
            if fName.endswith("A"):
                self.writeA(os.path.join(dirName, fName))

            if fName.endswith("D"):
                self.writeD(os.path.join(dirName, fName))

            zFile.write(fName)
            os.remove(fName)
            print("done!")

        print("Packing unmodified files:", end="")

        for file in os.listdir(dirName):
            if not (file in ("map-AirA", "map-AirD", "map-CableA", "map-CableD")):
                zFile.write(os.path.join(dirName, file), file)
                print(file, end="")

            os.remove(os.path.join(dirName, file))
        print("done!")

        zFile.close()

        print("All done!")


class scmFileF(scmFile):
    def __init__(self):
        formatA = [('Available', 'b'), ('Used', 'b'), ('Skip', 'b'), ('Source', 'b'), ('Signal', 'b'),
                   ('Modulation', 'b'), ('Locked', 'b'), ('Unknown7', 'b'), ('Tuned', 'b'), ('Number', 'h'),
                   ('Unknown11', 'b'), ('Unknown12', 'l'), ('Preset', 'h'), ('Length', 'h'), ('Name', '12s'),
                   ('Frequency', 'f'), ('Favorite1', 'l'), ('Favorite2', 'l'), ('Favorite3', 'l'),
                   ('Favorite4', 'l'), ('Favorites5', 'l'), ('Unknown35', 'l'), ('Unknown36', 'b'), ('Unknown37', 'b'),
                   ('Unknown38', 'B'), ('CRC', 'B')]

        formatD = [('Number', 'h'), ('VID_PID', 'h'), ('PCR_PID', 'h'), ('SID', 'H'), ('Skip', 'b'), ('Unknown9', 'b'),
                   ('Source', 'b'), ('Signal', 'b'), ('Modulation', 'b'), ('Unknown13', 'b'), ('Bandwidth', 'b'),
                   ('Type', 'B'), ('VideoCodec', 'b'), ('Unknown17', 'b'), ('Unknown18', 'b'), ('Unknown19', 'b'),
                   ('VideoWidth', 'h'), ('VideoHeight', 'h'), ('Scrambled', 'b'), ('FrameRate', 'b'),
                   ('Unknown26', 'b'), ('Unknown27', 'b'), ('SymbolRate', 'h'), ('Unknown30', 'b'), ('Locked', 'b'),
                   ('ONID', 'H'), ('NID', 'H'), ('Unknown36', 'l'), ('Provider', 'h'), ('Channel', 'H'), ('LCN', 'h'),
                   ('Unknown46', 'h'), ('TSID', 'H'), ('Unknown50', '6s'), ('Unknown56', 'l'), ('Unknown60', 'l'),
                   ('Name', '200s'), ('Short', '18s'), ('VideoFormat', 'b'), ('Unknown283', 'b'), ('Unknown284', 'l'),
                   ('Unknown288', 'h'), ('Unknown219', 'h'), ('Favorites1', 'l'), ('Favorites2', 'l'),
                   ('Favorites3', 'l'), ('Favorites4', 'l'), ('Favorites5', 'l'), ('Unknown312', 'l'),
                   ('Unknown316', 'h'), ('Unknown318', 'B'), ('CRC', 'B')]

        super(scmFileF, self).__init__(formatA, formatD)
        pass


class scmFileC(scmFile):
    def __init__(self):
        formatA = [('Available', 'b'), ('Used', 'b'), ('Skip', 'b'), ('Source', 'b'), ('Signal', 'b'),
                   ('Modulation', 'b'), ('Locked', 'b'), ('Unknown7', 'b'), ('Tuned', 'b'), ('Number', 'h'),
                   ('Unknown11', 'b'), ('Unknown12', 'l'), ('Preset', 'h'), ('Length', 'h'), ('Name', '12s'),
                   ('Frequency', 'f'), ('Favorites1', 'l'), ('Favorites2', 'l'), ('Favorites3', 'l'),
                   ('Favorites4', 'l'), ('Favorites5', 'l'), ('Unknown35', 'l'), ('Unknown36', 'b'), ('Unknown37', 'b'),
                   ('Unknown38', 'B'), ('CRC', 'B')]
        formatD = [('Number', 'h'), ('VID_PID', 'h'), ('PCR_PID', 'h'), ('SID', 'H'), ('Unknown8', 'b'),
                   ('Unknown9', 'b'), ('Source', 'b'), ('Signal', 'b'), ('Modulation', 'b'), ('Unknown13', 'b'),
                   ('Bandwidth', 'b'), ('Type', 'B'), ('VideoCodec', 'b'), ('Unknown17', 'b'), ('Unknown18', 'b'),
                   ('Unknown19', 'b'), ('VideoWidth', 'h'), ('VideoHeight', 'h'), ('Scrambled', 'b'),
                   ('FrameRate', 'b'), ('Unknown26', 'b'), ('Unknown27', 'b'), ('SymbolRate', 'h'), ('Unknown30', 'b'),
                   ('Locked', 'b'), ('ONID', 'H'), ('NID', 'H'), ('Unknown36', 'l'), ('Provider', 'h'),
                   ('Channel', 'H'), ('LCN', 'h'), ('Unknown46', 'h'), ('TSID', 'H'), ('Unknown50', '6s'),
                   ('Unknown56', 'l'), ('Unknown60', 'l'), ('Name', '200s'), ('Short', '18s'), ('VideoFormat', 'b'),
                   ('Unknown283', 'b'), ('Unknown284', 'l'), ('Unknown288', 'h'), ('Favorites', 'B'), ('CRC', 'B')]
        super(scmFileC, self).__init__(formatA, formatD)
