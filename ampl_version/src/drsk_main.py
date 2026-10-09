import math
import time
from amplpy import AMPL
from myutils import breakexit
from log import danoLogger
from drsk_ampl import read_and_store, solve
from drsk_boosting import evalPhi_greedy
from drsk_separation import addCut_greedy, addCut_quasiGreedy

relative_tol = .01  #TODO: should be read in

def drsk_logIteration(log, x, cost, Phi_L, Phi_max):
    log.joint("  > Cost:    %g\n"%cost)
    log.joint("  > Phi_L:   %g\n"%Phi_L)
    log.joint("  > Phi_max: %g\n"%Phi_max)
    log.joint("  Solution:\n")
    for var_name, var_val in x.items():
        if math.fabs(var_val) > 1e-8:
            log.joint("    %s = %g\n"%(var_name, var_val))
    log.joint("===============================================================\n\n")


start_time = t0 = time.time()    
def drsk_algoLoop(alldata):
    log = alldata['log']

    for iteration in range(11):
        alldata['algo_data']['iteration'] = iteration

        # Solve the master problem for optimal (x, Phi_L)
        solve(alldata)
        x = alldata['algo_data']['soln_vector_dict']
        Phi_L = alldata['algo_data']['Phi_L']
        cost = alldata['algo_data']['cost']
        if alldata['breakpoints']: breakexit('Solved master problem')

        # Boosting step: Evaluate Phi(x*) and get z
        Phi_max = evalPhi_greedy(alldata, alldata['algo_data']["soln_vector_dict"])
        if alldata['breakpoints']: breakexit('Completed boosting step: evaluated Phi and stored z')

        # Convergence check
        if (Phi_max - Phi_L) / Phi_max <= relative_tol:
            log.joint("CONVERGED: achieved relative tolerance\n")
            drsk_logIteration(log, x, cost, Phi_L, Phi_max)
            break

        # Add cut
        addCut_greedy(alldata)
        if alldata['breakpoints']: breakexit('Computed cut')

        # Log progress
        log.joint("Completed iteration %d\n"%iteration)
        drsk_logIteration(log, x, cost, Phi_L, Phi_max)
        if alldata['breakpoints']: breakexit('Run next iteration?')

    # Log results
    end_time = time.time()
    elapsed_time = end_time - start_time
    log.joint("Algorithm FINISHED after %d iterations in %g seconds\n"%(iteration, elapsed_time))




def drsk_start(log_file, mod_file, cut_file):
    alldata = {}
    log = alldata['log'] = danoLogger(log_file)
    alldata['MODFILE'] = mod_file
    alldata['CUTFILE'] = cut_file
    alldata['loud'] = True
    alldata['verbose'] = True
    alldata['breakpoints'] = False
    log.joint("MODFILE %s\n"%alldata['MODFILE'])
    log.joint("CUTFILE %s\n"%alldata['CUTFILE'])

    # Initialize prob data
    alldata['prob_data'] = {}                     # All problem related data stored here
    alldata['prob_data']['Theta'] = 100.0           # Theta value for weighted objective parameter
    alldata['prob_data']['constraints'] = []      # List of all constraints
    alldata['prob_data']['features'] = []         # List of features, i.e., constraint with risky coefficients
    alldata['prob_data']['variables'] = {}        # Dictionary: variable name --> variable index (exluding artifical and dummy
    alldata["prob_data"]['all_constr_data'] = {}  # Dictionary: constraint name --> constraint data
    log.joint("Theta %g\n"%alldata['prob_data']['Theta'])

    # Initialize coefficient risk structure
    alldata["struct_data"] = {}                 # All risky coefficient structure data stored here
    alldata["struct_data"]["numfeats"] = 0      # Number of features (constraints with risky coefficients)
    alldata["struct_data"]["risky_coeffs"] = {} # Dictionary: coefficient --> coefficient data (index, zvar, instances)
    alldata["struct_data"]['num_unique'] = 0    # Number of unique risky coefficients
    alldata["struct_data"]['budget'] = .01      # Constraint error budget
    log.joint("budget %g\n"%alldata['struct_data']['budget'])

    # Initialize cut data TODO: should be read in from cutfile
    alldata['cut_data'] = {}                                # All cut related data stored here
    alldata['cut_data']['maxcuts'] = 100                                # Maximum number of cuts TODO: read in
    alldata['cut_data']['numcuts'] = 0                      # Number of cuts to use in solve
    alldata['cut_data']['nonzero_cutweights'] = set()       # Set: (cut number, feat name) pairs with nonzero weight
    alldata['cut_data']['cutweights'] = {}                  # Dict: (cut number, feat name) --> weight
    alldata['cut_data']['nonzero_phiQuadWeights'] = set()   # Set: (cut number, feat name, var name, var name) tuples with nonzero weight
    alldata['cut_data']['phiQuadWeights'] = {}              # Quadratic weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, va name, var name) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiLinWeights'] = set()    # Set: (cut number, feat name, var naem) tuples with nonzero weight
    alldata['cut_data']['phiLinWeights'] = {}               # Linear weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiConstWeights'] = set()  # Set: (cut number, feat name) tuples with nonzero weight
    alldata['cut_data']['phiConstWeights'] = {}             # Constants defining phi_i(.|z). Dict: (cut number, feature name) --> constant
    alldata['cut_data']['phiMinusToggle'] = {}              # Toggle for whether the minus constraint is needed in phi definition for this cut and feature
    log.joint("maxcuts %g\n"%alldata['cut_data']['maxcuts'])

    # Initialize algorithm data (Note: extra greedy specific algo data defined in greedy Phi method)
    alldata['algo_data'] = {}  # all algorithm related data stored here
    alldata['algo_data']['ampl'] = AMPL()
    alldata['algo_data']['alpha'] = 1.0
    alldata['algo_data']['phi_scale'] = 'percent_violation'  #'scaled_abs_violation'
    alldata['algo_data']['solver'] = 'gurobi' #"/Applications/knitro-16.0.0-ARM-MacOS/bin/knitroampl"
    alldata['algo_data']['soln_vector_dict'] = {}
    alldata['algo_data']['Phi_L'] = 0.0
    alldata['algo_data']['cost'] = 0.0
    alldata['algo_data']['iteration'] = 0
    log.joint("alpha %g\n"%alldata['algo_data']['alpha'])
    log.joint("phi_scale %s\n"%alldata['algo_data']['phi_scale'])
    log.joint("solver %s\n"%alldata['algo_data']['solver'])
    if alldata['breakpoints']: ('Done initializing all data')


    # Retrieve problem data and risk structure
    read_and_store(alldata)
    if alldata['breakpoints']: breakexit('Done parsing problem')

    drsk_algoLoop(alldata)

    