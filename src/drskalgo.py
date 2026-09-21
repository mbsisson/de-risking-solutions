import time
import numpy as np
from myutils import breakexit
from drsk import drsk_add_impactvar, drsk_add_greedycuts, drsk_getimpact_greedy, drsk_add_softmaxcuts, drsk_getimpact_softmax
from drsklp import drsk_solveLP, drsk_writeSol, drsk_getobjectivevalue, drsk_writeLP

def drsk_greedy(alldata):
    '''Runs SOFTMAX-ADVERSARIAL algorithm using the greedy method for the boosting step'''
    log = alldata['log']
    log.joint("Running Greedy.\n")
    loud = alldata.get('loud', 0)
    start_time = time.time()

    retcode = 0
    condition = ('greedy')

    I = alldata['structure']['I']
    alldata['algo']['impacts'] = np.zeros(I)
    alldata['algo']['indmax'] = np.zeros(I, dtype=int)
    alldata['algo']['zvalues'] = np.zeros(I)

    # Additional memory for logging
    alldata['algo']['maxriskyterms'] = {}
    alldata['algo']['senses'] = np.zeros(I, dtype=str)
    alldata['algo']['slacks'] = np.zeros(I)
    alldata['algo']['RHSs'] = np.zeros(I)
    alldata['algo']['max_percent_violations'] = np.zeros(I)
    alldata['algo']['max_scaled_abs_violations'] = np.zeros(I)

    tol = alldata['algo']['tol']
    maxits = alldata['algo']['maxits']
    iteration = alldata['algo']['iteration_cnt'] = 0
    solutionvectordict = alldata['solutionvectordictionary']

    done = False
    while not done:
        alldata['algo']['iterations'][iteration] = {}

        # Solve master problem
        retcode, condition = drsk_solveLP(alldata)
        if retcode:
            log.joint('solveLP returns %d, %s at iter %d.\n' %(retcode, condition, iteration))
            return retcode, condition
        alldata['algo']['iterations'][iteration]['solution'] = solutionvectordict.copy()
        drsk_writeSol(alldata, solutionvectordict)  #optional: write soltuion to file

        # Get objective value and cost
        objval, cost = drsk_getobjectivevalue(alldata, solutionvectordict, loud = 0)
        alldata['algo']['iterations'][iteration]['objval'] = objval
        alldata['algo']['iterations'][iteration]['cost'] = cost

        # Get Phi_L
        Phi_L = solutionvectordict.get('Phi_L', 0.0)
        alldata['algo']['iterations'][iteration]['Phi_L'] = Phi_L

        # Compute the phi_max (z^t is greedy)
        phi_max = drsk_getimpact_greedy(alldata, solutionvectordict, loud=loud)
        alldata['algo']['iterations'][iteration]['phi_max']  = phi_max

        # Log objective and impact values
        runtime = time.time() - start_time
        alldata['algo']['iterations'][iteration]['runtime'] = runtime
        log.joint('Iteration %d.  Obj %.5g  Cost %.5g  Phi_L %.5g  phi_max %.5g  Runtime %.5g.\n' %(iteration, objval, cost, Phi_L, phi_max, runtime))
        if iteration > 0:
            c_0 = alldata['algo']['iterations'][0]['cost']
            phi_max_initial = alldata['algo']['iterations'][0]['phi_max']
            log.joint('  > %.4f increase over original cost %.2f\n'%(cost / c_0, c_0))
            log.joint('  > %.4f decrease from original phi_max %.2f\n'%(phi_max / phi_max_initial, phi_max_initial))

        if iteration == 0: 
        # Add Phi_L to model, if first iteration (need first impact value to tune weights)
            retcode, condition = drsk_add_impactvar(alldata)
            if retcode:
                log.joint('add_impactvar returns %d at iter %d.\n' %(retcode, iteration))
                return retcode, condition

        # Convergence check
        if (phi_max - Phi_L) / phi_max < tol:
            log.joint('  DONE: impact converged\n')
            break
        # Optional: early convergence check: Phi_L < lambda_hi * Phi(x^0)
        # elif phi_max < alldata['algo']['lambda_hi'] * alldata['algo']['iterations'][0]['phi_max']:
        #     log.joint('  DONE: impact < {} * {} = lambda_hi * impact(x^0)\n'.format(alldata['algo']['lambda_hi'], alldata['algo']['iterations'][0]['phi_max']))
        #     break
        elif iteration >= maxits:
            log.joint('  DONE: max iteration reached.\n')
            break
        else:
            log.joint('  NOTDONE: keep running.\n')

        # Add greedy cuts
        retcode, condition = drsk_add_greedycuts(alldata, loud=loud)
        if retcode:
            log.joint('add_greedy returns %d at iter %d.\n' %(retcode, iteration))
            return retcode, condition

        #breakexit('iteration %d complete'%iteration)
        iteration += 1
        alldata['algo']['iteration_cnt'] = iteration

        # write LP to file (optional)
        retcode = drsk_writeLP(alldata)
        

    breakexit('Done running Greedy algo.')
    log.joint('\n')

    # Log iterations
    log.joint('ITERATION SUMMARY:\n')
    for i in range(min(iteration, maxits)+1):
        objval = float(alldata['algo']['iterations'][i]['objval'])
        cost = float(alldata['algo']['iterations'][i]['cost'])
        Phi_L = float(alldata['algo']['iterations'][i]['Phi_L'])
        phi_max = float(alldata['algo']['iterations'][i]['phi_max'])
        runtime = float(alldata['algo']['iterations'][i]['runtime'])
        log.joint('  Iteration %d   Objval %10.10f   Cost %10.10f   Phi_L %10.10f   phi_max %10.10f   runtime %.3f\n'%(i, objval, cost, Phi_L, phi_max, runtime))
    log.joint('\n')

    c_0 = alldata['algo']['iterations'][0]['cost']
    imp_0 = alldata['algo']['iterations'][0]['phi_max']
    c_last = alldata['algo']['iterations'][iteration]['cost']
    imp_last = alldata['algo']['iterations'][iteration]['phi_max']
    log.joint('Impact Decrease (lambda): %g\n'%(imp_last / imp_0))
    log.joint('Cost Increase (multiplier): %g\n'%(c_last / c_0))

    # if not alldata['algo']['givenTheta']:
    #     targetObj = c_0 + alldata['algo']['theta'] * alldata['algo']['lambda_hi'] * imp_0
    #     log.joint('Target Objective value : %10.10f   (i.e. c(x*) + \Theta \lambda^hi \Phi(x*))\n'%(targetObj))
    #     if objval <= targetObj:
    #         log.joint('  Final objval is smaller --> achieved desired impact decrease for small cost increase.\n')
    #     else:
    #         log.joint('  Final objval is larger --> no such point with desired impact and cost exists.\n')

    #     log.joint(' phi_max %10.10f   desired_impact %10.10f\n'%(phi_max, alldata['algo']['targetimpact']))
    #     log.joint(' cost %10.10f   desired_cost %10.10f\n'%(cost, alldata['algo']['targetcost']))

    breakexit('results.')



    ### Interpolate ###
    # log.joint('Interpolating soltuion...\n')
    # # Compute midpoint of x* and algorithm solution
    # interpolatedsolution = {}
    # for v in model.getVars():
    #     v_star = alldata['algo']['iterations'][0]['solution'].get(v.varname, 0.0)
    #     v_algo = alldata['algo']['iterations'][iteration]['solution'][v.varname]
    #     interpolatedsolution[v.varname] = .5*v_star + .5*v_algo
    # drsk_writeSol(alldata, interpolatedsolution, "interpolated.sol")
    # # Get objval and cost
    # objval_interp, cost_interp = drsk_getobjectivevalue(alldata, interpolatedsolution, loud=0)
    # # Get impact on interpolated solution
    # phi_max_interp = drsk_getimpact(alldata, interpolatedsolution)

    # log.joint('Interpolated Soltuion:\n')
    # log.joint('  Obj %10.10g   Cost %10.10g   Max-Impact %10.10g.\n' %(objval_interp, cost_interp, phi_max_interp))
    # # determine lambda, \Phi(x_interp) = \lambda * \Phi(x_star)
    # log.joint('  lambda: %g\n'%(phi_max_interp / imp_0))

    # breakexit('Interpolated Solution')
    return retcode, condition



def drsk_softmax(alldata):
    retcode = 0
    condition = ('SOFTMAX-ADVERSARIAL')
    log = alldata['log']
    model = alldata['gurobimodel']

    log.joint("Running SOFTMAX-ADVERSARIAL.\n")

    #alldata['algo']['deltas'] = np.zeros(alldata['structure']['I'])
    #alldata['algo']['indmax'] = np.zeros(alldata['structure']['I'], dtype=int)
    #alldata['algo']['zvalues'] = np.zeros(alldata['structure']['I'])

    tol = alldata['algo']['tol']
    iteration = alldata['algo']['iteration_cnt'] = 0
    maxits = alldata['algo']['maxits']
    solutionvectordict = alldata['solutionvectordictionary']

    while iteration < maxits:
        alldata['algo']['iterations'][iteration] = {}

        # Solve LP
        retcode, condition = drsk_solveLP(alldata)
        if retcode:
            log.joint('solveLP returns %d, %s at iter %d.\n' %(retcode, condition, iteration))
            return retcode, condition
        drsk_writeSol(alldata, solutionvectordict) #optional: write soltuion to file

        # Get objective value and cost
        objval, cost = drsk_getobjectivevalue(alldata, solutionvectordict, loud = 0)
        alldata['algo']['iterations'][iteration]['objval'] = objval
        alldata['algo']['iterations'][iteration]['cost'] = cost

        # Get Phi_L
        Phi_L = solutionvectordict.get('Phi_L', 0.0)
        alldata['algo']['iterations'][iteration]['Phi_L'] = Phi_L

        # Compute the phi_max (z^t is via softmax)
        phi_max = drsk_getimpact_softmax(alldata, solutionvectordict)
        alldata['algo']['iterations'][iteration]['phi_max'] = phi_max
        breakexit('computed impact')

        # Log objective and impact values
        log.joint('Iteration %d.  Obj %.5g  Cost %.5g  Phi_L %.5g  Max-Impact %.5g.\n' %(iteration, objval, cost, Phi_L, phi_max))
        if iteration > 0:
            c_0 = alldata['algo']['iterations'][0]['cost']
            phi_max_initial = alldata['algo']['iterations'][0]['phi_max']
            log.joint('  > %.4f increase over original cost %.2f\n'%(cost / c_0, c_0))
            log.joint('  > %.4f decrease from original phi_max %.2f\n'%phi_max / phi_max_initial, phi_max_initial)

        if iteration == 0: 
        # Add impact variable, Phi_L, if first iteration (need first impact value to tune weights) TODO: move before loop somehow
            retcode, condition = drsk_add_impactvar(alldata)
            if retcode:
                log.joint('add_impactvar returns %d at iter %d.\n' %(retcode, iteration))
                return retcode, condition

        # Convergence check
        if (phi_max - Phi_L) / phi_max < tol:
            log.joint('  DONE: impact converged\n')
            break
        else:
            log.joint('  NOTDONE: keep running.\n')

        # Add greedy cuts
        retcode, condition = drsk_add_softmaxcuts(alldata)
        if retcode:
            log.joint('add_greedy returns %d at iter %d.\n' %(retcode, iteration))
            return retcode, condition

        breakexit('iteration %d complete'%iteration)
        iteration += 1
        alldata['algo']['iteration_cnt'] = iteration

        # write LP to file (optional)
        retcode = drsk_writeLP(alldata)

    breakexit('Done running SOFTMAX-ADVERSARIAL.')
    log.joint('\n')

    # Log iterations
    log.joint('ITERATION SUMMARY:\n')
    for i in range(min(iteration+1, maxits)):
        objval = float(alldata['algo']['iterations'][i]['objval'])
        cost = float(alldata['algo']['iterations'][i]['cost'])
        Phi_L = float(alldata['algo']['iterations'][i]['Phi_L'])
        phi_max = float(alldata['algo']['iterations'][i]['phi_max'])
        log.joint('  Iteration %d   Objval %10.10f   Cost %10.10f   Phi_L %10.10f   Max-Impact %10.10f\n'%(i, objval, cost, Phi_L, phi_max))
    log.joint('\n')

    c_0 = alldata['algo']['iterations'][0]['cost']
    imp_0 = alldata['algo']['iterations'][0]['phi_max']
    c_last = alldata['algo']['iterations'][iteration]['cost']
    imp_last = alldata['algo']['iterations'][iteration]['phi_max']
    log.joint('Impact Decrease (lambda): %g\n'%(imp_last / imp_0))
    log.joint('Cost Increase (multiplier): %g\n'%(c_last / c_0))

    if not alldata['algo']['givenTheta']:
        targetObj = c_0 + alldata['algo']['theta'] * alldata['algo']['lambda_hi'] * imp_0
        log.joint('Target Objective value : %10.10f   (i.e. c(x*) + Theta lambda^hi Phi(x*))\n'%(targetObj))
        if objval <= targetObj:
            log.joint('  Final objval is samller --> achieved desired impact decrease for small cost increase.\n')
        else:
            log.joint('  Final objval is larger --> no such point with desired impact and cost exists.\n')

        log.joint(' maximpact %10.10f   desired_impact %10.10f\n'%(phi_max, alldata['algo']['targetimpact']))
        log.joint(' cost %10.10f   desired_cost %10.10f\n'%(cost, alldata['algo']['targetcost']))

    breakexit('results.')
    return retcode, condition