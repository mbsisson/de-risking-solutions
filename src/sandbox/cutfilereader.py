import sys
################################################
# Necessary for scripts in src/sandbox/
from pathlib import Path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))
################################################
from myutils import breakexit


def read_cutfile(all_data, filename):
    log = all_data['log']
    maxcuts = all_data['maxcuts']

    log.joint("Reading cut file: " + filename + "\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    all_data['numimpcuts'] = 0
    cutnonzeros = all_data['cutnonzeros'] = []
    matrixvalue = all_data['matrixvalue'] = {}

    linenum = 0
    thisline = lines[linenum].split()
    readnumcuts = int(thisline[0])
    if maxcuts < 0:
        numcuts = readnumcuts                                                                     
    else:
        numcuts = min(maxcuts, readnumcuts)

    all_data['numcuts'] = numcuts
    log.joint('Using %d cuts.\n' %numcuts)
    breakexit('num cuts')

    Theta = all_data['Theta'] = float(thisline[3])
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