import sys
import os.path

def simplebreak():
    stuff = input('break > ')
    if stuff == 'x' or stuff == 'q':
        sys.exit("bye")

def breakexit(foo):
    stuff = input("("+foo+") break> ")
    if stuff == 'x' or stuff == 'q':
        sys.exit("bye")
def returnbreakexit(foo):
    stuff = input("("+foo+") break> ")
    if stuff == 'x' or stuff == 'q':
        return 1
    else:
        return 0

def askfordouble(foo):
    stuff = input("("+foo+") input value> ")
    value = float(stuff)
    return value

def checkstop(log,name):
    if os.path.isfile(name) :
        breakexit("stop?")

def myprintfile(log, mfilename, casefilelines):
    try:
        f = open(mfilename, "w")
    except:
        log.stateandquit("cannot open file " + mfilename + "\n")

    for line in casefilelines.values():
        f.write(line)

    f.close()

    return 1

def myreadfile(log, filename):
    code = 0
    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.joint("cannot open file " + filename + "\n")
        code = 1

    return code, lines

def myshownparray(log, array, arraylen, arrayname, padding=""):
    log.joint("%s: \n" %(arrayname))

    k = 0
    for h in range(arraylen):
        if k == 0: log.joint("%s"%(padding))
        log.joint('%.3e ' %(array[h]))
        k += 1
        if k == 10:
            log.joint("\n")
            k = 0
    if k>0: log.joint("\n")

def myshownparraythresh(log, array, arraylen, arrayname, thresh=0.0, padding=""):
    log.joint("%s: \n" %(arrayname))

    for h in range(arraylen):
        if array[h] > thresh:
            log.joint('%s[%d] %.3e\n' %(padding, h, array[h]))
