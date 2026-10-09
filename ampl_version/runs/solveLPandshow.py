#!/usr/bin/python

import sys
import math
from gurobipy import *
from datetime import date
import time

if len(sys.argv) < 2:
    print('Usage: solveLPandshow.py lpfilename')
    exit(0)

if len(sys.argv) >= 3:
    logfilename = sys.argv[2]
else: logfilename = 'solveLPandshow.log'
log = open(logfilename,"w")

today = date.today()


# Read and solve model

model = read(sys.argv[1])
#model.params.Cuts = 0
#model.params.presolve = 0
#model.params.NonConvex = 2
t0 = time.time()
model.optimize()
t1 = time.time()
runtime = t1 - t0

log.write('Solving %s\n' % sys.argv[1])
log.write("variables = " + str(model.NumVars) + "\n")
log.write("constraints = " + str(model.NumConstrs) + "\n")

stringvalue = 'none'
success = False

if model.status == GRB.status.INF_OR_UNBD:
    #logger.joint('->LP infeasible or unbounded\n')
    model.Params.DualReductions = 0
    t0p = time.time()
    model.optimize()
    t1p = time.time()

    runtime += t1p - t0p
if model.status == GRB.status.INFEASIBLE:
    #logger.joint('->LP infeasible')
    stringvalue = 'INFEASIBLE'
    model.computeIIS()
    model.write("model.ilp")
        
elif model.status == GRB.status.UNBOUNDED:
    #logger.joint('->LP unbounded')
    stringvalue = 'UNBOUNDED'
elif model.status == GRB.OPTIMAL:
    #logger.joint(' OPTIMAL for {:s}, optimal value: {:.4e} in time {:.4e}'.format(signature, model.objval, t1-t0))
    success = True
    stringvalue = 'OPTIMAL'

elif model.status == GRB.SUBOPTIMAL:
    #logger.joint(' SUBOPTIMAL for {:s}, (sub)optimal value: {:.4e} in time {:.4e}'.format(signature, model.objval, t1-t0))
    success = True
    stringvalue = 'SUBOPTIMAL'
else:
    #logger.joint(' unexpected status ' + str(model.status))
    stringvalue = 'UNEXPECTED'

if success:
    log.write('Optimal objective = %g\n' % model.objVal)
    log.write('Optimal variable values:\n')
    print('Optimal variable values:')
    count = 0
    for v in model.getVars():
        #print(v.varname)
        if math.fabs(v.x) > 0.00000001:
            log.write('%s = %.16e\n'%(v.varname,v.x))
            print(v.varname,"=",v.x)
            count += 1
        
    # Be sure to print IMP anyways
    IMP = model.getVarByName("imp")
    if not IMP:
        IMP = model.getVarByName("IMP")
    if IMP:
        log.write('\n')
        print()
        log.write('Impact varible (in case below threshold):\n')
        print('Impact varible (in case below threshold):')
        log.write('  IMP = %g\n'%(IMP.x))
        print('  IMP =', IMP.x)
            

    log.write(str(count) + " nonzero variables in solution\n")
log.write("bye.\n")
log.close()
