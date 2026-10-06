from amplpy import AMPL
from myutils import breakexit
from log import danoLogger
from drsk_ampl import read_and_store, solve
from drsk_greedy import eval_Phi_greedy, add_cut_greedy

def drsk(log_file, mod_file, cut_file):
    alldata = {}
    alldata['log'] = danoLogger(log_file)
    alldata['MODFILE'] = mod_file
    alldata['CUTFILE'] = cut_file
    alldata['loud'] = True

    # Initialize prob data TODO: maybe should be read automatically inside readandstore()
    alldata['prob_data'] = {}  # All problem related data stored here
    alldata['prob_data']['Theta'] = 0.0
    alldata['prob_data']['features'] = [f"e{i}" for i in range(2, 210)]  #TODO inside readandstore()
    #alldata['prob_data']['var_indicies'] = list(range(2, 19))  #TODO inside readandstore()
    alldata['prob_data']['variables'] = {}  # Dictionary: variable name --> variable index (exluding artifical and dummy)
    alldata['prob_data']['constraints'] = [f"e{i}" for i in range(2, 210)]  #TODO inside readandstore() NOT SAME as features
    alldata["prob_data"]['all_constr_data'] = {}  # Dictionary: constraint name --> constraint data
    # Read unchanging problem data into ampl

    # Initialize coefficient risk structure
    alldata["struct_data"] = {}  # All risky coeff. structure data stored here
    alldata["struct_data"]["numfeats"] = 0  # Number features (constraints with risky coefficients)
    alldata["struct_data"]["risky_coeffs"] = {}  # TODO
    alldata["struct_data"]['num_unique'] = 0  # Number of unique risky coefficients
    alldata["struct_data"]['budget'] = .01  # Constraint error budget

    # Initialize cut data TODO: should be read in from cutfile
    alldata['cut_data'] = {}                                # All cut related data stored here
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
    # Read cut file
    # alldata['maxcuts'] = 100
    # log.joint("Max number of cuts = %d\n"%alldata['maxcuts'])
    # read_cutfile(alldata, alldata['CUTFILE'])

    # Initialize algorithm data
    alldata['algo_data'] = {}  # all algorithm related data stored here
    alldata['algo_data']['ampl'] = AMPL()
    alldata['algo_data']['alpha'] = 1.0
    alldata['algo_data']['phi_scale'] = 'percent_violation'  #'scaled_abs_violation'
    alldata['algo_data']["solver"] = 'gurobi' #"/Applications/knitro-16.0.0-ARM-MacOS/bin/knitroampl"
    alldata['algo_data']["soln_vector_dict"] = {}
    # Note: extra greedy specific algo data defined in greedy Phi method

    ###########################################################################

    # Retrieve problem data and risk structure
    read_and_store(alldata)
    # TODO: first read variables, features, structure... then add vars, params, constraints to modfile... then ampl read that file
    breakexit('Done parsing problem')

    # Solve and get solution x*
    solve(alldata)
    breakexit('Done solving problem')

    # Evaluate Phi(x*) and get z
    Phi = eval_Phi_greedy(alldata, alldata['algo_data']["soln_vector_dict"])
    breakexit('Evaluated Phi')

    # Add cut
    add_cut_greedy(alldata)
    breakexit('Computed cut')

    # Solve and get next iterate solution xt
    solve(alldata)
    breakexit('Done solving problem')