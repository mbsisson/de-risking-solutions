import sys
from myutils import breakexit


def read_cutfile(alldata, filename):
    log = alldata['log']
    maxcuts = alldata['maxcuts']

    log.joint("Reading cut file: " + filename + "\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    alldata['numimpcuts'] = 0
    cutnonzeros = alldata['cutnonzeros'] = []
    matrixvalue = alldata['matrixvalue'] = {}

    linenum = 0
    thisline = lines[linenum].split()
    readnumcuts = int(thisline[0])
    if maxcuts < 0:
        numcuts = readnumcuts                                                                     
    else:
        numcuts = min(maxcuts, readnumcuts)

    alldata['numcuts'] = numcuts
    log.joint('Using %d cuts.\n' %numcuts)
    breakexit('num cuts')

    Theta = alldata['Theta'] = float(thisline[3])
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))
    for cutnum in range(1, numcuts+1):
        linenum += 1
        thisline = lines[linenum].split()
        quant = int(thisline[3])

        for _ in range(1, quant+1):
            linenum += 1
            thisline = lines[linenum].split()
            featnum = int(thisline[0])
            coeff = float(thisline[1])
            cutnonzeros.append((cutnum, featnum))
            matrixvalue[(cutnum, featnum)] = coeff

        linenum += 1 #empty row