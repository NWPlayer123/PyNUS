#from __future__ import print_function
from requests import get
from cStringIO import StringIO
from os.path import exists
from os import mkdir
from struct import unpack
from binascii import hexlify, unhexlify
import sys

global path, base, tmd, info
base = "http://nus.cdn.shop.wii.com/ccs/download/"

def validateTitleID(tid):
    try:
        if b'-' in tid:
            tid = tid.translate(None, b'-')
        assert len(tid) == 16
        assert tid[:4] == "0005" #Wii U
        tid = tid.upper()
    except:
        raise BaseException("Not a valid Title ID: " + tid)
        sys.exit(0)
    return tid

def downloadTMD(tid, ver=None):
    tmd = StringIO()
    if not exists(path + "/title.tmd"):
        print("Downloading title.tmd for " + tid)
        request = get(base + tid + "/tmd")
        with open(path + "/title.tmd", "wb") as f:
            for chunk in request.iter_content(1024):
                if chunk: tmd.write(chunk)
            tmd.seek(0);f.write(tmd.read())
    else:
        print("TMD already exists, continuing")
        with open(path + "/title.tmd", "rb") as f:
            tmd.write(f.read())
    tmd.seek(0)
    return tmd

def downloadChunk(tid, name, size):
    name = name.upper()
    if not exists(path + "/" + name or path + "/" + name + ".app"):
        sys.stdout.write("Downloading chunk " + name + ": 00%\r")
        request = get(base + tid + "/" + name, stream=True)
        tick = 0
        count = int(size / 100.0)
        update = count
        with open(path + "/" + name + ".app", "wb") as f:
            for chunk in request.iter_content(1024):
                if chunk:
                    f.write(chunk)
                    tick += 1024
                if tick > update:
                    update += count
                    sys.stdout.write("Downloading chunk " + name + ": " +
                        "%02d" % int(tick / count) + "%\r")
        try:
            request = get(base + tid + "/" + name + ".h3")
            with open(path + "/" + name + ".h3", "wb") as f:
                for chunk in request.iter_content(1024):
                    if chunk: f.write(chunk)
        except: pass
    else: print("Chunk " + name + " already exists, continuing")

def firstBoot():
    if not exists("titles"):
        mkdir("titles")
    if not exists("data"):
        mkdir("data")
    with open("data/config.txt", "wb") as f:
        f.write("firstBoot = True\r\n")

def makePath(tid):
    tid = [tid[:8], tid[8:]]
    
    path = "titles/" + tid[0]
    if not exists(path):
        mkdir(path) #Easier to find schtuff

    path += "/" + tid[1]
    if not exists(path):
        mkdir(path)

    return path

def parseTMD(tmd):
    tmd.seek(0x1DE) #hardcoded, probs bad
    count = unpack(">H", tmd.read(2))[0]
    print("Content count: " + str(count))
    tmd.seek(0xB04)
    info = []
    for i in range(count):
        data = [a for a in unpack(">IHHQ", tmd.read(16))]
        data.append(hexlify(tmd.read(0x20)))
        info.append(data)
        print("%08X" % data[0] + ": " + calcSize(data[3]))
    return info

def calcSize(size):
    if size < 1024:
        return str(size) + " bytes"
    else:
        size /= 1024.0
        if size < 1024.0:
            return '{:>6}'.format(round(size, 3)) + " KB"
        else:
            size /= 1024.0
            if size < 1024.0:
                return '{:>6}'.format(round(size, 2)) + " MB"
            else:
                size /= 1024.0
                if size < 1024.0:
                    return '{:>6}'.format(round(size, 2)) + " GB"
                else: raise Exception("This should never happen")

if __name__ == "__main__":
    sys.argv.append("00050000-1010DB00")

    if not exists("data/config.txt"): firstBoot()
    tid = validateTitleID(sys.argv[1])
    path = makePath(tid)
    tmd = downloadTMD(tid)
    info = parseTMD(tmd)
    for i in info:
        downloadChunk(tid, "%08x" % i[0], i[3])
        sys.stdout.write("\r\n")
    #downloadChunk(tid, "00000022", 0x8000)
    '''r = get("http://nus.cdn.shop.wii.com/ccs/download/0005000010128F00/tmd")
    f = StringIO()
    for chunk in r.iter_content(1024):
        if chunk: f.write(chunk)'''

'''
Notes: get(url, stream=True)
http://stackoverflow.com/questions/16694907

'''
