###############################################################################
# Functions for running the main loop of SOFTMAX_-ADVERSARIAL algorithm.
#
# Blake Sisson mbs2246@columbia.edu
# 10/14/2026
###############################################################################
import math
import time
from myutils import breakexit
from drsk_ampl import drsk_run_solver
from drsk_boosting import drsk_evalPhi_greedy
from drsk_separation import drsk_addCut_greedy, drsk_addCut_quasiGreedy


def logIteration(log, x, cost, Phi_L, Phi_max):
    log.joint("  > Cost:    %g\n"%cost)
    log.joint("  > Phi_L:   %g\n"%Phi_L)
    log.joint("  > Phi_max: %g\n"%Phi_max)
    log.joint("  Solution:\n")
    for var_name, var_val in x.items():
        if math.fabs(var_val) > 1e-8:
            log.joint("    %s = %g\n"%(var_name, var_val))
    log.joint("===============================================================\n\n")


def logResults(alldata, iteration, elapsed_time, convergence_flag):
    log = alldata['log']
    result_str = ""

    result_str += "Algorithm FINISHED after %d iterations in %g seconds\n"%(iteration, elapsed_time)

    # Report convergence reason
    if convergence_flag == 0:
        result_str += " *** Maximum iterations reached ***\n"
    elif convergence_flag == 1:
        result_str += " *** Achieved relative tolerance ***\n"
    elif convergence_flag == 2:
        result_str += " *** Reduced Phi_max by sufficient amount ***\n"

    # Report cost and phi differentials
    cost_initial = alldata['algo_data'][0]['cost']
    cost_final = alldata['algo_data'][iteration]['cost']
    cost_delta = (cost_final - cost_initial) / cost_initial
    Phi_max_initial = alldata['algo_data'][0]['Phi_max']
    Phi_max_final = alldata['algo_data'][iteration]['Phi_max']
    Phi_max_delta = abs(Phi_max_final - Phi_max_initial) / Phi_max_initial
    result_str += " > Percent cost increase: %g\n"%cost_delta
    result_str += " > Percent Phi_max decrease: %g\n"%Phi_max_delta
    
    # Log header
    headers = ['Iter', 'Cost', 'Phi_L', 'Phi_max', 'time']
    col_widths = [6, 20, 20, 20, 8]
    header_row = "".join(f"{headers[col]:<{col_widths[col]}}" for col in range(len(headers)))
    result_str += "%s\n"%header_row
    result_str += "-" * len(header_row) + "\n"

    # Log results per iteration
    for i in range(iteration + 1):
        cost = alldata['algo_data'][i]['cost']
        Phi_L = alldata['algo_data'][i]['Phi_L']
        Phi_max = alldata['algo_data'][i]['Phi_max']
        t = alldata['algo_data'][i]['time']
        row = [str(i), f"{cost:.12f}", f"{Phi_L:.12f}", f"{Phi_max:.12f}", f"{t:.4f}"]
        row_str = "".join(f"{row[col]:<{col_widths[col]}}" for col in range(len(headers)))
        result_str += "%s\n"%row_str

    log.joint(result_str)
    return result_str


def setTheta(alldata, cost_0, Phi_max_0):
    log = alldata['log']
    lam_hi = alldata['prob_data']['lam_hi']
    lam_lo = alldata['prob_data']['lam_lo']
    xi = alldata['prob_data']['xi']
    alldata['prob_data']['Theta'] = (cost_0 * xi) / (Phi_max_0 * (lam_hi - lam_lo))
    log.joint('Set Theta to %g\n'%alldata['prob_data']['Theta'])


def drsk_algoLoop(alldata):
    retcode = 0

    log = alldata['log']
    relative_tol = alldata['algo_data']['tol']
    maxits = alldata['algo_data']['maxits']
    Phi_reduction_goal = alldata['algo_data']['PhiReduc']
    zerothresh = alldata['algo_data']['zerothresh']

    # Record how algorithm terminates: 0 = reached maxit, 1 = converged, 2 = early convergence (reduced phi_max)
    converge_flag = 0

    start_algo_time = time.time()
    for iteration in range(maxits + 1):
        alldata['algo_data']['iteration'] = iteration
        alldata['algo_data'][iteration] = {}
        start_iter_time = time.time()

        # Solve the master problem for optimal (x, Phi_L)
        solvecode =  drsk_run_solver(alldata)
        x = alldata['algo_data']['soln_vector_dict']
        Phi_L = alldata['algo_data']['Phi_L']
        cost = alldata['algo_data']['cost']
        if alldata['breakpoints']: breakexit('Solved master problem')

        # Boosting step: Evaluate Phi(x*) and get z
        Phi_max = drsk_evalPhi_greedy(alldata, alldata['algo_data']["soln_vector_dict"])
        if alldata['breakpoints']: breakexit('Completed boosting step: evaluated Phi and stored z')

        # Set using nominal solution after first iteration IF Theta set to auto
        if iteration == 0 and alldata['prob_data']['autoTheta']:
            setTheta(alldata, cost, Phi_max)

        # Store iteration
        end_iter_time = time.time()
        alldata['algo_data'][iteration]['cost'] = cost
        alldata['algo_data'][iteration]['Phi_L'] = Phi_L
        alldata['algo_data'][iteration]['Phi_max'] = Phi_max
        alldata['algo_data'][iteration]['time'] = end_iter_time - start_iter_time

        # Log progress
        log.joint("Completed iteration %d\n"%iteration)
        logIteration(log, x, cost, Phi_L, Phi_max)

        # Convergence check
        if Phi_max <= zerothresh or (Phi_max - Phi_L) / Phi_max <= relative_tol:
            log.joint("CONVERGED: achieved relative tolerance\n")
            logIteration(log, x, cost, Phi_L, Phi_max)
            converge_flag = 1
            break

        # Early convergence check
        if Phi_max <= Phi_reduction_goal * alldata['algo_data'][0]['Phi_max']:
            log.joint("CONVERGED: reduced Phi_max by sufficient amount\n")
            logIteration(log, x, cost, Phi_L, Phi_max)
            converge_flag = 2
            break

        if solvecode:
            log.joint("STOP: solver taking too long\n")
            retcode = 1
            break

        # Add cut
        log.joint("Did NOT converge: add cut\n")
        drsk_addCut_greedy(alldata)
        if alldata['breakpoints']: breakexit('Computed cut. Run next iteration?')

    if retcode:
        return 'Solver takes too long\n'

    # Log results
    end_algo_time = time.time()
    elapsed_time = end_algo_time - start_algo_time
    return logResults(alldata, iteration, elapsed_time, converge_flag)
