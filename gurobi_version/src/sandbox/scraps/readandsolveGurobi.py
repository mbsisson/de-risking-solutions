import sys

################################################
# Necessary for scripts in src/sandbox/
from pathlib import Path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))
################################################

from log import danoLogger
from myutils import breakexit
from drsklp import drsk_solveLP
from riskycoefficients import drsk_getlp, drsk_storelp



if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('usage: readandsolveGurobi.py LPfile')

    alldata = {}
    alldata['LPFILE'] = sys.argv[1]
    log = alldata['log'] = danoLogger('readandsolveGurobi.log')
    alldata['loud'] = True

    # Read LP into Gurob
    drsk_getlp(alldata)
    drsk_storelp(alldata)
    breakexit('Done reading problem')

    # Allocate memory for solution
    solutionvectordictionary = {}
    gurobimodel = alldata['gurobimodel']  
    for var in gurobimodel.getVars():
        solutionvectordictionary[var.varname] = 0
    alldata['solutionvectordictionary'] = solutionvectordictionary

    # Solve LP with Gurobi
    retcode, condition = drsk_solveLP(alldata)
    if retcode:
        log.joint('solveLP returns %d, %s.\n' %(retcode, condition))
        sys.exit(1)
    log.joint(f"Max violation: {gurobimodel.ConstrVio}\n")
    breakexit('Solved problem with Gurobi')

    # Save solution
    #drsk_writeSol(alldata, solutionvectordict)  
