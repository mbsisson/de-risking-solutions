import sys
import time
import math
from amplpy import AMPL

################################################
# Necessary for scripts in src/sandbox/
from pathlib import Path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))
################################################
from myutils import breakexit
from log import danoLogger
from parseampl import readandstore
from drsk_ampl import eval_Phi_greedy
from cutfilereader import read_cutfile


def solve(alldata):
    log = alldata['log']
    ampl = alldata['algo_data']['ampl']
    solver = alldata['algo_data']['solver']
    variables = alldata['prob_data']['variables']
    constraints = alldata['prob_data']['constraints']
    soln_vector_dict = alldata['algo_data']['soln_vector_dict']

    # Read in all parameters and sets
    ampl.get_parameter("Theta").set(alldata['prob_data']['Theta'])
    ampl.get_parameter("numcuts").set(alldata['cut_data']['numcuts'])
    ampl.get_set("nonzero_cutweights").set_values(alldata['cut_data']['nonzero_cutweights'])
    ampl.get_parameter("CutWeights").set_values(alldata['cut_data']['cutweights'])
    ampl.get_parameter("phiQuadCoeffs").set_values(alldata['cut_data']['quad_data'])
    ampl.get_parameter("phiLinCoeffs").set_values(alldata['cut_data']['lin_data'])
    ampl.get_parameter("phiConstants").set_values(alldata['cut_data']['const_data'])

    # Set solver
    ampl.setOption('solver', solver)
    log.joint("Using solver: %s\n"%solver)

    # Solve                                                                                                                              
    log.joint("Solving model ...\n")                                                                                                    
    t0 = time.time()                                                                                                                     
    ampl.solve()                                                                                                                         
    t1 = time.time()
    log.joint("===============================================================\n")                                                    
    log.joint("===============================================================\n\n")
    log.joint("Solved with %s in %f seconds\n"%(solver, t1-t0))

    # Store solution
    for name, objective in ampl.get_objectives():
        log.joint('Optimal objective: %s = %g\n' % (name, objective.value()))
    log.joint('Optimal variable values:\n')
    count = 0
    for v in variables:
        # Store solution
        soln_vector_dict[v] = ampl.get_value(v)

        # Log nonzero values
        if math.fabs(soln_vector_dict[v]) > 1e-8:
            log.joint('  %s = %g\n'%(v, soln_vector_dict[v]))
            count += 1
    log.joint(str(count) + " nonzero variables in solution\n\n")

    # Iterate through all constraints to find violations
    log.joint("Checking for violations...\n")
    count = 0
    for constr_name in constraints:
        #Check if the constraint is violated (negative slack means the bound is breached)
        constraint = ampl.get_constraint(constr_name)
        if constraint.slack() < -1e-6:
            count += 1
            log.joint(f"  Violation in {name}:\n")
            log.joint(f"    Slack: {constraint.slack()}\n")
            log.joint(f"    Lower Bound: {constraint.lb()}, Upper Bound: {constraint.ub()}\n")
    log.joint(str(count) + " constraints violated\n\n")


def add_cut_greedy(alldata):
    log = alldata['log']
    loud = alldata['loud']
    all_constr_data = alldata['prob_data']['all_constr_data']
    structure = alldata['struct_data']
    budget = structure['budget']
    alpha = alldata['algo_data']['alpha']

    alldata['cut_data']['numcuts'] += 1
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']  # set: (cut number, feat name) pairs with nonzero weight
    cutweights = alldata['cut_data']['cutweights']  # Dict: (cut number, feat name) --> weight
    nonzero_quad_data = alldata['cut_data']['nonzero_quad_data']  # set: (cut number, feat name, var index, var index) tuples with nonzero weight
    quad_data = alldata['cut_data']['quad_data']  # Quadratic coefficients defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var index, var index) --> coefficient * (1 + z)
    nonzero_lin_data = alldata['cut_data']['nonzero_lin_data']  # set: (cut number, feat name, var index) tuples with nonzero weight
    lin_data = alldata['cut_data']['lin_data']  # Linear coefficients defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var index) --> coefficient * (1 + z)
    nonzero_const_data = alldata['cut_data']['nonzero_const_data'] = {}  # set: (cut number, feat name) tuples with nonzero weight
    const_data = alldata['cut_data']['const_data']  # Constants defining phi_i(.|z), which are cut independent. Dict: feature name --> constant

    maxPhi = alldata['algo_data']['maxPhi']
    argmax_constr = alldata['algo_data']['argmax_constr']
    argmax_zsign = alldata['algo_data']['argmax_zsign']
    argmax_zvar = alldata['algo_data']['argmax_zvar']
    argmax_coeff = alldata['algo_data']['argmax_coeff']
    argmax_phis = alldata['algo_data']['argmax_phis']

    cutnum = alldata['cut_data']['numcuts']

    # Compute weight normalizer
    sum_exp = 0.0
    for _, phi in argmax_phis.items():
        sum_exp += math.exp(alpha * phi)

    # Compute and set cut weights
    for feat_name, phi in argmax_phis.items():
        nonzero_cutweights.add((cutnum, feat_name))
        cutweights[(cutnum, feat_name)] = math.exp(alpha * phi) / sum_exp

    # Retrieve coefficient data for each nonzero feature
    for feat_name, phi in argmax_phis.items():
        constraint_data = all_constr_data[feat_name]

        # Set constant
        nonzero_const_data.add((cutnum, feat_name))
        const_data[(cutnum, feat_name)] = constraint_data['constant']

        # Set linear coefficients
        for var, coeff in constraint_data['lin_terms'].items():
            nonzero_lin_data.add((cutnum, feat_name, var))
            lin_data[(cutnum, feat_name, var)] = coeff

        # Set quadratic coefficients
        for var_tuple, coeff in constraint_data['quad_terms'].items():
            v1, v2 = var_tuple[0], var_tuple[1]
            nonzero_quad_data.add((cutnum, feat_name, v1, v2))
            quad_data[(cutnum, feat_name, v1, v2)] = coeff

    # Add budget to argmax_zvar terms

    # Scale all coefficients by phi_scale
    

    log.joint("Adding greedy cut\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: ampl_test.py modfile cutfile')

    alldata = {}
    log = alldata['log'] = danoLogger('ampl_test.log')
    alldata['loud'] = False

    # Get files from arguments
    alldata['MODFILE'] = sys.argv[1]
    alldata['CUTFILE'] = 'cutsrun.dat' if len(sys.argv) == 2 else sys.argv[2]

    # Initialize prob data TODO: maybe should be read automatically inside readandstore()
    alldata['prob_data'] = {}  # All problem related data stored here
    alldata['prob_data']['Theta'] = 0.0
    alldata['prob_data']['features'] = [f"e{i}" for i in range(2, 210)]  #TODO inside readandstore()
    #alldata['prob_data']['var_indicies'] = list(range(2, 19))  #TODO inside readandstore()
    alldata['prob_data']['variables'] = []  # List of variable names (exluding artifical and dummy)
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
    alldata['cut_data'] = {}  #  All cut related data stored here
    alldata['cut_data']['numcuts'] = 0  # Number of cuts to use in solve
    alldata['cut_data']['nonzero_cutweights'] = {}  # set: (cut number, feat name) pairs with nonzero weight
    alldata['cut_data']['cutweights'] = {}  # Dict: (cut number, feat name) --> weight
    alldata['cut_data']['nonzero_quad_data'] = {}  # set: (cut number, feat name, var, var) tuples with nonzero weight
    alldata['cut_data']['quad_data'] = {}  # Quadratic coefficients defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var, var) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_lin_data'] = {}  # set: (cut number, feat name, var) tuples with nonzero weight
    alldata['cut_data']['lin_data'] = {}  # Linear coefficients defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_const_data'] = {}  # set: (cut number, feat name) tuples with nonzero weight
    alldata['cut_data']['const_data'] = {}  # Constants defining phi_i(.|z). Dict: (cut number, feature name) --> constant
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
    readandstore(alldata)
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

