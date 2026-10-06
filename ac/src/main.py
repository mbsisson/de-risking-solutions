###############################################################################
##                                                                           ##
## This code was is an extension of work by Matias Villagra,         ##
## former PhD Student in Operations Research @ Columbia, supervised by              ##
## Daniel Bienstock.                                                         ##
##                                                                           ##
## June 2026
###############################################################################

import sys
import os
import time
import reader
from myutils import breakexit
from versioner import *
from log import danoLogger
from ac import *
from socp import *


def read_cutfile(all_data, filename):
    log = all_data['log']
    maxcuts = all_data['maxcuts']

    log.joint("reading cut file " + filename + "\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    linenum       = 0
    all_data['numimpcuts'] = 0
    cutnonzeros = all_data['cutnonzeros'] = []
    matrixvalue = all_data['matrixvalue'] = {}
    impcuts = all_data['impcuts'] = {}
    lenimpcuts = all_data['lenimpcuts'] = {}    
    thisline = lines[linenum].split()
    readnumcuts = int(thisline[0])
    if maxcuts < 0:
        numcuts = readnumcuts
    else:
        numcuts = min(maxcuts, readnumcuts)
    all_data['numcuts'] = numcuts
    print(readnumcuts, maxcuts)
    log.joint('Using %d cuts.\n' %numcuts)
    breakexit('numc')
    
    Theta = all_data['Theta'] = float(thisline[3])
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))
    for h in range(1, numcuts+1):
        impcuts[h] = []
        linenum += 1
        thisline = lines[linenum].split()
        quant = int(thisline[3])
        lenimpcuts[h] = quant
        #log.joint('cut %d of length %d.\n' %(h,lenimpcuts[h]))
        for i in range(1, quant+1):
            linenum += 1
            thisline = lines[linenum].split()            
            j = int(thisline[0])
            coeff = float(thisline[1])
            impcuts[h].append((j,coeff))
            cutnonzeros.append((h,j))
            matrixvalue[(h,j)] = coeff
        #print(impcuts[h])
        linenum += 1 #empty row            
    #breakexit('cutfile')

def read_config(log, filename):

    log.joint("reading config file " + filename + "\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    casefilename      = '../data/none'
    modfile           = '../data/none'
    cutfilename       = 'cuts.dat'
    solver            = 'knitroampl'
    multistart        = 0
    writesol          = 0
    expand            = 0
    max_time          = 1000
    mode              = ['default']
    maxcuts           = -1 #default
    
    linenum       = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0:

            if thisline[0] == 'casefilename':
                casefilename  = thisline[1]

            elif thisline[0] == 'modfile':
                modfile       = thisline[1]
                
            elif thisline[0] == 'lpfilename':
                lpfilename    = thisline[1]

            elif thisline[0] == 'cutfilename':
                cutfilename    = thisline[1]
                if len(thisline) > 2:
                    maxcuts = int( thisline[2] )

            elif thisline[0] == 'solver':
                solver        = thisline[1]

            elif thisline[0] == 'mode':
                mode          = thisline[1:]

            elif thisline[0] == 'multistart':
                multistart    = 1

            elif thisline[0] == 'writesol':
                writesol    = 1

            elif thisline[0] == 'expand':
                expand      = 1

            elif thisline[0] == 'max_time':
                max_time      = int(thisline[1])                                      
                
            elif thisline[0] == 'END':
                break

            else:
                sys.exit("illegal input " + thisline[0] + "bye")

        linenum += 1

    all_data                      = {}
    all_data['casefilename']      = casefilename
    all_data['cutfilename']       = cutfilename
    all_data['maxcuts']           = maxcuts
    all_data['casename']          = casefilename.split('data/')[1].split('.m')[0]
    all_data['modfile']           = modfile.split('../modfiles/')[1]
    all_data['solver']            = solver
    all_data['multistart']        = multistart
    all_data['writesol']          = writesol
    all_data['expand']            = expand
    all_data['max_time']          = max_time
    all_data['mode']              = mode
    
    return all_data

if __name__ == '__main__':
    if len(sys.argv) > 3 or len(sys.argv) < 2:
        print ('Usage: main.py file.config [logfile]\n')
        exit(0)

    T0        = time.time()
    mylogfile = "main.log"

    if len(sys.argv) == 3:
        mylogfile = sys.argv[2]  # Optional logfile

    log = danoLogger(mylogfile)
    stateversion(log)

    all_data       = read_config(log,sys.argv[1])
    all_data['T0'] = T0

    all_data['log'] = log
    
    readcode = reader.readcase(log,all_data,all_data['casefilename'])

    read_cutfile(all_data, all_data['cutfilename'])

    if True: #all_data['modfile'] == 'ac.mod':
        if all_data['solver'] != 'knitro' and all_data['solver'] != 'rocky':
            log.joint('Wrong solver/modfile, please check config file\n')
            exit(1)
        else:
            goac(log,all_data)
        
    elif all_data['modfile'] == 'jabr.mod':
        if all_data['solver'] != 'mosek':
            gosocp(log,all_data)
        else:
            log.joint('Wrong solver/modfile, please check config file\n')
            exit(1)

    elif all_data['modfile'] == 'jabr_mosek.mod':
        if all_data['solver'] == 'mosek':
            gosocp_mosek(log,all_data)
        else:
            log.joint('Wrong solver/modfile, please check config file\n')
            exit(1)            
            
    elif all_data['modfile'] == 'i2.mod':
        if all_data['solver'] != 'mosek':
            gosocp2(log,all_data)
        else:
            log.joint('Wrong solver/modfile, please check config file\n')
            exit(1)

    elif all_data['modfile'] == 'i2_mosek.mod':
        if all_data['solver'] == 'mosek':
            gosocp2_mosek(log,all_data)
        else:
            log.joint('Wrong solver/modfile, please check config file\n')
            exit(1)
            
    else:
        log.joint('Wrong solver/modfile, please check config file\n')
        exit(1)
        
    log.closelog()

