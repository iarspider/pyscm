import struct
from collections import OrderedDict
import sys
import os
import zipfile
import re
from io import StringIO


class scmFile(object):
    def __init__(self):
        self.ifile = None
        self.ofile = None
        self.formatA = None
        self.keyzA = None
        self.formatD = None
        self.keyzD = None

    @staticmethod
    def bytes2utf16(data):
        return data.rstrip('\x00').decode('utf16-be')

    def parseA(self, data):
        valz = struct.unpack(self.formatA, data)
        chan = OrderedDict(zip(self.keyzA, valz))

        if chan['Length'] == 0:
            chan['Name'] = ''
        else:
            chan['Name'] = self.bytes2utf16(chan['Name'])

        self.ofile.write(";".join(map(str, chan.values())) + "\n")

    def packA(self, valz):
        # TODO: No numeric indices please!
        name = valz[14].ljust(12, '\x00')
        valz[14] = name.encode("utf_16_be")
        if len(name) == 0:
            valz[13] = 0
        else:
            valz[13] = 12  # length - always 12?

        valz[19] = '0'  # crc

        for i, x in enumerate(valz):
            try:
                valz[i] = int(x)
            except ValueError:
                valz[i] = x

        valz[15] = float(valz[15])

        data = struct.pack(self.formatA, *valz)

        # Calculate CRC
        crc = sum(data) & 0xFF
        valz[19] = crc
        data = struct.pack(self.formatA, *valz)
        self.ofile.write(data)

    def parseD(self, data):
        valz = struct.unpack(self.formatD, data)
        chan = OrderedDict(zip(self.keyzD, valz))

        chan['Name'] = self.bytes2utf16(chan['Name'])
        chan['Short'] = self.bytes2utf16(chan['Short'])

        if chan['Name'] != "":
            for k, v in chan.iteritems():
                print(k, ' = "', v, '"')

        self.ofile.write(";".join(map(str, chan.values())) + "\n")

    def packD(self, valz):
        # TODO: No numeric indexes

        name = valz[36].ljust(200, '\x00')
        valz[36] = name.encode("utf_16_be")
        short = valz[37].rjust(18, '\x00')
        valz[37] = short.encode("utf_16_be")

        valz[33] = '\x00' * 6
        valz[43] = 0

        for i, x in enumerate(valz):
            try:
                valz[i] = int(x)
            except ValueError:
                valz[i] = x

        data = struct.pack(self.formatD, *valz)

        # Calculate CRC
        crc = sum(data) & 0xFF
        valz[43] = crc
        data = struct.pack(self.formatD, *valz)
        self.ofile.write(data)

    def readA(self, ofilename):
        #		print "Decoding to {0}...".format(ofilename),

        # f = open("map-AirA", "rb")
        self.ofile = open(ofilename, "w")
        self.ofile.write(";".join(map(str, self.keyzA)) + "\n")

        while (True):
            data = self.ifile.read(40)
            if (len(data) != 40):
                #				print "done!"
                break
            self.parseA(data)

        self.ofile.close()

    def writeA(self, ofilename):
        #		print "Packing {0}...".format(ofilename),
        self.ofile = open(ofilename, "wb")
        self.ifile = open(ofilename + '.csv', "r")
        self.ifile.readline()
        while (True):
            d = self.ifile.readline().strip()
            if (len(d) > 0):
                self.packA(d.split(";"))
            else:
                #				print "done!"
                break

        self.ofile.close()

    def readD(self, ofilename):
        #		print "Decoding to {0}...".format(ofilename),

        self.ofile = open(ofilename, "w")
        self.ofile.write(";".join(map(str, self.keyzD)) + "\n")

        while (True):
            data = self.ifile.read(292)
            if (len(data) != 292):
                #				print "done!"
                break
            self.parseD(data)

        self.ofile.close()

    def writeD(self, ofilename):
        #		print "Packing {0}...".format(ofilename),
        self.ofile = open(ofilename, "wb")
        self.ifile = open(ofilename + '.csv', "r")
        self.ifile.readline()
        while (True):
            d = self.ifile.readline().strip()
            if (len(d) > 0):
                self.packD(d.split(";"))
            else:
                #				print "done!"
                break

        self.ofile.close()
        self.ifile.close()

    def readSCM(self):
        zName = ""
        for xName in os.listdir("."):
            if (re.match(r"channel_list_.+_[0-9]{4}\.scm", xName)):
                zName = xName
                break

        if (zName == ""):
            print
            "ERROR: No scm file(s) found!"
            sys.exit(0)

        print
        "Unpacking files from {0}:".format(zName)

        zFile = zipfile.ZipFile(zName, "r")
        for fName in ("map-AirA", "map-AirD", "map-CableA", "map-CableD"):
            print
            "\t" + fName + "...",
            # zFile.extract(fName)
            data = zFile.read(fName)
            self.ifile = StringIO.StringIO(data)
            if (fName.endswith('A')):
                self.readA(fName + '.csv')

            if (fName.endswith('D')):
                self.readD(fName + '.csv')
            print
            "done!"

        print
        "All done!"
        zFile.close()

    def writeSCM(self):
        zName = ""
        for xName in os.listdir("."):
            if (re.match(r"channel_list_.+_[0-9]{4}\.scm", xName)):
                zName = xName
                break

        if (zName == ""):
            print
            "ERROR: No scm file(s) found!"
            sys.exit(0)

        print
        "Creating temporary directory to store unchanged files...",
        os.mkdir("ztmp")
        print
        "done!"

        print
        "Unpacking all files from {0}...".format(zName),
        zFile = zipfile.ZipFile(zName, "r")
        zFile.extractall("ztmp")
        zFile.close()
        print
        "done!"

        zFile = zipfile.ZipFile(zName, "w", zipfile.ZIP_DEFLATED)

        print
        "Packing modified files:"
        for fName in ("map-AirA", "map-AirD", "map-CableA", "map-CableD"):
            print
            "\t" + fName + "...",
            if (fName.endswith("A")):
                self.writeA(fName)

            if (fName.endswith("D")):
                self.writeD(fName)

            zFile.write(fName)
            os.remove(fName)
            print
            "done!"

        print
        "Packing unmodified files:",
        for file in os.listdir("ztmp"):
            if not (file in ("map-AirA", "map-AirD", "map-CableA", "map-CableD")):
                zFile.write(os.path.join("ztmp", file), file)
                print
                file,
            os.remove(os.path.join("ztmp", file))
        print
        "done!"

        print
        "Removing temporary directory...",
        os.rmdir("ztmp")
        zFile.close()
        print
        "done!"

        print
        "All done!"
class scmFileF:
    def __init__(self):
        self.keyzA = ['Available', 'Used', 'Skip', 'Source', 'Signal', 'Modulation', 'Locked', 'Unknown7',
                      'Tuned', 'Number', 'Unknown11', 'Unknown12', 'Preset', 'Length', 'Name', 'Frequency',
                      'Favorites1', 'Favorites2', 'Favorites3', 'Favorites4', 'Favorites5', 'Unknown35',
                      'Unknown36', 'Unknown37', 'Unknown38', 'CRC']
        self.keyzD = ["Number", "VID_PID", "PCR_PID", "SID", "Unknown8", "Unknown9", "Source", "Signal",
        #             
                      "Modulation", "Unknown13", "Bandwidth", "Type", "VideoCodec", "Unknown17", "Unknown18",
                      "Unknown19", "VideoWidth", "VideoHeight", "Scrambled", "FrameRate", "Unknown26",
                      "Unknown27", "SymbolRate", "Unknown30", "Locked", "ONID", "NID", "Unknown36",
                      "Provider", "Channel", "LCN", "Unknown46", "TSID", "Unknown50", "Unknown56", "Unknown60",
                      "Name", "Short", "VideoFormat", "Unknown283", "Unknown284", "Unknown288", "Favorites", "CRC"]
        self.formatA = "<bbbbbbbbbhblhh12sfllllllbbBB"
        self.formatD = "<hhhHbbbbbbbBbbbbhhbbbbhbbHHlhHhhH6sll200s18sbblhBB"
        pass




if __name__ == "__main__":
    if (len(sys.argv) != 2) or (sys.argv[1].lower() != 'read' and sys.argv[1].lower() != 'write'):
        print
        "Usage: runme.py read - to decode channel list"
        print
        "       runme.py write - to reencode channel list"
        sys.exit(0)

    scm = scmFile()

    if (sys.argv[1].lower() == 'write'):
        scm.writeSCM()
    # os.remove("map-AirA.csv")
    #	os.remove("map-AirD.csv")
    #	os.remove("map-CableA.csv")
    #	os.remove("map-CableD.csv")
    else:
        scm.readSCM()
