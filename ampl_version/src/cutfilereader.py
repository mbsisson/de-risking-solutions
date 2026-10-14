###############################################################################
# Functions for reading cut files and writing cut data to file
#
# Blake Sisson mbs2246@columbia.edu
# 10/7/2026
###############################################################################
import sys
from myutils import breakexit


def read_cutfile(alldata, filename):
    log = alldata['log']
    log.joint("Reading cut file: " + filename + "\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    # Data structures to populate
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']
    nonzero_phiQuadweights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    # Retrieve max cuts
    maxcuts = alldata['cut_data']['maxcuts']

    # First line is how many cuts to read
    linenum = 0
    thisline = lines[linenum].split()
    readnumcuts = int(thisline[0])
    if maxcuts < 0:
        numcuts = readnumcuts                                                                     
    else:
        numcuts = min(maxcuts, readnumcuts)

    alldata['cut_data']['numcuts'] = numcuts
    log.joint('Using %d cuts.\n' %numcuts)
    if alldata['breakpoints']: breakexit('num cuts')

    Theta = alldata['prob_data']['Theta'] = float(thisline[3])
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))

    for cutnum in range(1, numcuts+1):
        linenum += 2   # first line is just cut count

        # Read cutweights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            weight = float(thisline[1])
            nonzero_cutweights.append((cutnum, featname))
            cutweights[(cutnum, featname)] = weight

        # Read phiQuadWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            var1idx = thisline[1]
            var2idx = thisline[2]
            weight = float(thisline[3])
            nonzero_phiQuadweights.append((cutnum, featname, var1idx, var2idx))
            phiQuadWeights[(cutnum, featname, var1idx, var2idx)] = weight

        # Read phiLinWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            varidx = thisline[1]
            weight = float(thisline[2])
            nonzero_phiLinWeights.append((cutnum, featname, varidx))
            phiLinWeights[(cutnum, featname, varidx)] = weight

        # Read phiConstWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            weight = float(thisline[1])
            phiConstWeights[(cutnum, featname)] = weight

        # Read phiMinusToggle
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            toggle = int(thisline[1])
            phiMinusToggle[(cutnum, featname)] = toggle

        linenum += 1 #empty row


def write_cutfile(alldata, filename):
    log = alldata['log']
    log.joint("Writing cut file: " + filename + "\n")

    try:
        f = open(filename, "w")
    except:
        log.stateandquit("cannot write to file %s\n" %(filename))
        sys.exit(1)

    # Data structures to write
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']
    nonzero_phiQuadWeights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    numcuts = alldata['cut_data']['numcuts']
    log.joint('Writing %d cuts.\n' %numcuts)
    if alldata['breakpoints']: breakexit('num cuts')

    Theta = alldata['prob_data']['Theta']
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))
    f.write('%d Cuts Theta %g\n'%(numcuts, Theta))

    for cutnum in range(1, numcuts+1):
        f.write('Cut %d\n'%cutnum)

        # Write cutweights
        these_nonzero_cutweights = [tuple for tuple in nonzero_cutweights if tuple[0] == cutnum]
        count = len(these_nonzero_cutweights)
        f.write('  cutweights len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            weight = cutweights[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, weight))

        # Write phiQuadWeights
        these_nonzero_phiQuadWeights = [tuple for tuple in nonzero_phiQuadWeights if tuple[0] == cutnum]
        count = len(these_nonzero_phiQuadWeights)
        f.write('  phiQuadWeights len %d\n'%count)
        for tuple in these_nonzero_phiQuadWeights:
            featname = tuple[1]
            var1idx = tuple[2]
            var2idx = tuple[3]
            weight = phiQuadWeights[(cutnum, featname, var1idx, var2idx)]
            f.write('    %s %d %d %g\n'%(featname, var1idx, var2idx, weight))

        # Write phiLinWeights
        these_nonzero_phiLinWeights = [tuple for tuple in nonzero_phiLinWeights if tuple[0] == cutnum]
        count = len(these_nonzero_phiLinWeights)
        f.write('  phiLinWeights len %d\n'%count)
        for tuple in these_nonzero_phiLinWeights:
            featname = tuple[1]
            varidx = tuple[2]
            weight = phiLinWeights[(cutnum, featname, varidx)]
            f.write('    %s %d %g\n'%(featname, varidx, weight))

        # Read phiConstWeights
        count = len(these_nonzero_cutweights)
        f.write('  phiConstWeights len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            weight = phiConstWeights[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, weight))

        # Read phiMinusToggle
        count = len(these_nonzero_cutweights)
        f.write('  phiMinusToggle len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            toggle = phiMinusToggle[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, toggle))

        f.write('\n')

    # Close writier
    f.close()