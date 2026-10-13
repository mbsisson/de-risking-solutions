###############################################################################
# Functions for initializing all data necessary for SOFTMAX_-ADVERSARIAL
# algorithm and running the main loop.
#
# Blake Sisson mbs2246@columbia.edu
# 10/13/2026
###############################################################################

import math
import time
from amplpy import AMPL
from myutils import breakexit
from drsk_ampl import read_and_store, solve
from drsk_boosting import evalPhi_greedy
from drsk_separation import addCut_greedy, addCut_quasiGreedy


def logIteration(log, x, cost, Phi_L, Phi_max):
    log.joint("  > Cost:    %g\n"%cost)
    log.joint("  > Phi_L:   %g\n"%Phi_L)
    log.joint("  > Phi_max: %g\n"%Phi_max)
    log.joint("  Solution:\n")
    for var_name, var_val in x.items():
        if math.fabs(var_val) > 1e-8:
            log.joint("    %s = %g\n"%(var_name, var_val))
    log.joint("===============================================================\n\n")


def logResults(alldata, iteration, elapsed_time):
    log = alldata['log']
    log.joint("Algorithm FINISHED after %d iterations in %g seconds\n"%(iteration, elapsed_time))

    col_width = 20
    headers = ['Iter', 'Cost', 'Phi_L', 'Phi_max', 'time']

    # Log header
    header_row = "".join(f"{col:<{col_width}}" for col in headers)
    log.joint("%s\n"%header_row)
    log.joint("-" * len(header_row) + "\n")

    # Log results per iteration
    for i in range(iteration):
        cost = alldata['algo_data'][i]['cost']
        Phi_L = alldata['algo_data'][i]['Phi_L']
        Phi_max = alldata['algo_data'][i]['Phi_max']
        t = alldata['algo_data'][i]['time']
        row = [i, cost, Phi_L, Phi_max, t]
        log.joint("".join(f"{str(col):<{col_width}}" for col in row) + "\n")


def drsk_algoLoop(alldata):
    log = alldata['log']
    relative_tol = alldata['algo_data']['tol']
    maxits = alldata['algo_data']['maxits']

    start_algo_time = time.time()
    for iteration in range(maxits + 1):
        alldata['algo_data']['iteration'] = iteration
        alldata['algo_data'][iteration] = {}
        start_iter_time = time.time()

        # Solve the master problem for optimal (x, Phi_L)
        solve(alldata)
        x = alldata['algo_data']['soln_vector_dict']
        Phi_L = alldata['algo_data']['Phi_L']
        cost = alldata['algo_data']['cost']
        if alldata['breakpoints']: breakexit('Solved master problem')

        # Boosting step: Evaluate Phi(x*) and get z
        Phi_max = evalPhi_greedy(alldata, alldata['algo_data']["soln_vector_dict"])
        if alldata['breakpoints']: breakexit('Completed boosting step: evaluated Phi and stored z')

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
        if (Phi_max - Phi_L) / Phi_max <= relative_tol:
            log.joint("CONVERGED: achieved relative tolerance\n")
            logIteration(log, x, cost, Phi_L, Phi_max)
            break

        # Add cut
        log.joint("Did NOT converge: add cut\n")
        addCut_greedy(alldata)
        if alldata['breakpoints']: breakexit('Computed cut. Run next iteration?')

    # Log results
    end_algo_time = time.time()
    elapsed_time = end_algo_time - start_algo_time
    logResults(alldata, iteration, elapsed_time)


def drsk_readparameters(log, filename):
    '''Read parameters from file into local dictionary and return it'''
    log.joint("Reading parameter file " + filename + ".\n")
    params = {}

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    solver = 'None'
    theta = 'None'
    budget = 'None'
    phi_scale = 'None'
    alpha = 'None'
    decimal_risk_thresh = 'None'
    tol = 'None'
    maxits = 'None'
    loud = 0
    verbose = 0
    breakpoints = 0

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'solver':
                solver = thisline[1]
            elif word == 'theta':
                theta = float(thisline[1])
            elif word == 'budget':
                budget = float(thisline[1])
            elif word == 'phi_scale':
                phi_scale = thisline[1]
            elif word == 'alpha':
                alpha = float(thisline[1])
            elif word == 'decimal_risk_thresh':
                decimal_risk_thresh = int(thisline[1])
            elif word == 'tol':
                tol = float(thisline[1])
            elif word == 'maxits':
                maxits = int(thisline[1])
            elif word == 'maxits':
                maxits = int(thisline[1])
            elif word == 'loud':
                loud = int(thisline[1])
            elif word == 'verbose':
                verbose = int(thisline[1])
            elif word == 'breakpoints':
                breakpoints = int(thisline[1])
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + "\n")
                continue

        linenum += 1

    for x in [('solver', solver),
              ('theta', theta),
              ('budget', budget),
              ('phi_scale', phi_scale),
              ('alpha', alpha),
              ('decimal_risk_thresh', decimal_risk_thresh),
              ('tol', tol),
              ('maxits', maxits),
              ('loud', loud),
              ('verbose', verbose),
              ('breakpoints', breakpoints)]:
        if x[1] == 'NONE':
            log.stateandquit(' no ' + x[0] + ' input'+'\n')
        params[x[0]] = x[1]
        log.joint(x[0] + ' ' + str(x[1])+ '\n')

    return params


def drsk_start(logger, param_file, mod_file, cut_file):
    alldata = {}
    log = alldata['log'] = logger

    alldata['MODFILE'] = mod_file
    log.joint("MODFILE %s\n"%alldata['MODFILE'])
    alldata['CUTFILE'] = cut_file
    log.joint("CUTFILE %s\n"%alldata['CUTFILE'])
    alldata['PARAMFILE'] = param_file
    log.joint("PARAMFILE %s\n"%alldata['PARAMFILE'])

    # Read parameters
    params = drsk_readparameters(log, alldata['PARAMFILE'])

    # Set log output levels
    alldata['loud'] = params['loud']
    alldata['verbose'] = params['verbose']
    alldata['breakpoints'] = params['breakpoints']

    # Initialize prob data
    alldata['prob_data'] = {}                        # All problem related data stored here
    alldata['prob_data']['Theta'] = params['theta']  # Theta value for weighted objective parameter
    alldata['prob_data']['constraints'] = []         # List of all constraints
    alldata['prob_data']['features'] = []            # List of features, i.e., constraint with risky coefficients
    alldata['prob_data']['variables'] = {}           # Dictionary: variable name --> variable index (exluding artifical and dummy
    alldata["prob_data"]['all_constr_data'] = {}     # Dictionary: constraint name --> constraint data

    # Initialize coefficient risk structure
    alldata['struct_data'] = {}                                                     # All risky coefficient structure data stored here
    alldata['struct_data']["numfeats"] = 0                                          # Number of features (constraints with risky coefficients)
    alldata['struct_data']["risky_coeffs"] = {}                                     # Dictionary: coefficient --> coefficient data (index, zvar, instances)
    alldata['struct_data']['num_unique'] = 0                                        # Number of unique risky coefficients
    alldata['struct_data']['budget'] = params['budget']                             # Constraint error budget
    alldata['struct_data']['decimal_risk_thresh'] = params['decimal_risk_thresh']   # Number of decimal places coefficients need to be considered risky

    # Initialize cut data TODO: should be read in from cutfile
    alldata['cut_data'] = {}                                # All cut related data stored here
    alldata['cut_data']['maxcuts'] = 100                    # Maximum number of cuts TODO: read in
    alldata['cut_data']['numcuts'] = 0                      # Number of cuts to use in solve
    alldata['cut_data']['nonzero_cutweights'] = set()       # Set: (cut number, feat name) pairs with nonzero weight
    alldata['cut_data']['cutweights'] = {}                  # Dict: (cut number, feat name) --> weight
    alldata['cut_data']['nonzero_phiQuadWeights'] = set()   # Set: (cut number, feat name, var name, var name) tuples with nonzero weight
    alldata['cut_data']['phiQuadWeights'] = {}              # Quadratic weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, va name, var name) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiLinWeights'] = set()    # Set: (cut number, feat name, var name) tuples with nonzero weight
    alldata['cut_data']['phiLinWeights'] = {}               # Linear weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var vame) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiConstWeights'] = set()  # Set: (cut number, feat name) tuples with nonzero weight
    alldata['cut_data']['phiConstWeights'] = {}             # Constants defining phi_i(.|z). Dict: (cut number, feature name) --> constant
    alldata['cut_data']['phiMinusToggle'] = {}              # Toggle for whether the minus constraint is needed in phi definition for this cut and feature. Dict: (cut number, feat name, var) --> 0/1
    log.joint("maxcuts %g\n"%alldata['cut_data']['maxcuts'])

    # Initialize algorithm data (Note: extra greedy specific algo data defined in greedy Phi method)
    alldata['algo_data'] = {}                               # All algorithm related data stored here
    alldata['algo_data']['ampl'] = AMPL()                   # AMPL object  
    alldata['algo_data']['alpha'] = params['alpha']         # alpha value (for softmax)
    alldata['algo_data']['phi_scale'] = params['phi_scale'] # phi scale value, for scaling phi
    alldata['algo_data']['solver'] = params['solver']       # Solver to use
    alldata['algo_data']['soln_vector_dict'] = {}           # Solution dctionary: variable name --> value
    alldata['algo_data']['Phi_L'] = 0.0                     # Phi_L variable value
    alldata['algo_data']['cost'] = 0.0                      # Cost value in objective
    alldata['algo_data']['iteration'] = 0                   # Iteration number
    alldata['algo_data']['tol'] = params['tol']             # Relative convergence tolerance
    alldata['algo_data']['maxits'] = params['maxits']       # Maximum number of iterations

    if alldata['breakpoints']: breakexit('Done initializing all data')

    # Retrieve problem data and risk structure
    read_and_store(alldata)
    if alldata['breakpoints']: breakexit('Done parsing problem')

    drsk_algoLoop(alldata)

    