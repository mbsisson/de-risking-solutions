import sys
from datetime import datetime
from log import danoLogger
from drsk import drsk_getlp, drsk_checksolution
from drsklp import drsk_storelp
from drsk0 import drsk_readsolution


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit('usage: checksolution.py LPfile solutionfile')

    # Create logger
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    logfile = "checksolution_" + datetime_string + ".log"
    log = danoLogger(logfile)

    # Read config file
    alldata = {}
    alldata['log'] = log
    alldata['LPFILE'] = sys.argv[1]
    alldata['SOLFILE'] = sys.argv[2]
    alldata['NONZEROSINSOL'] = 1
    alldata['LOUDCONSTRAINTS'] = False

    # Read lp as gurobimodel
    drsk_getlp(alldata)

    # Read solution
    retcode = drsk_readsolution(alldata, alldata['SOLFILE'])
    if retcode:
        log.closelog()
        sys.exit('bye.')

    # Store all constraint data for LP
    drsk_storelp(alldata)
        
    # Check solution
    retcode = drsk_checksolution(alldata)
    log.joint('Solution checked with code %d.\n'%(retcode))

    
    log.closelog()    