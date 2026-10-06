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
    ampl.get_parameter("cutweights").set_values(alldata['cut_data']['cutweights'])
    ampl.get_set("nonzero_phiQuadWeights").set_values(alldata['cut_data']['nonzero_phiQuadWeights'])
    ampl.get_parameter("phiQuadWeights").set_values(alldata['cut_data']['phiQuadWeights'])
    ampl.get_set("nonzero_phiLinWeights").set_values(alldata['cut_data']['nonzero_phiLinWeights'])
    ampl.get_parameter("phiLinWeights").set_values(alldata['cut_data']['phiLinWeights'])
    ampl.get_set("nonzero_phiConstWeights").set_values(alldata['cut_data']['nonzero_phiConstWeights'])
    ampl.get_parameter("phiConstWeights").set_values(alldata['cut_data']['phiConstWeights'])
    ampl.get_parameter("phiMinusToggle").set_values(alldata['cut_data']['phiMinusToggle'])
    

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
    for v in variables.keys():
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
    variables = alldata['prob_data']['variables']
    structure = alldata['struct_data']
    budget = structure['budget']
    alpha = alldata['algo_data']['alpha']

    # Increment cut number
    alldata['cut_data']['numcuts'] += 1

    # Retrieve cut data to new cut to
    cutnum = alldata['cut_data']['numcuts']
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']
    nonzero_phiQuadWeights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    nonzero_phiConstWeights = alldata['cut_data']['nonzero_phiConstWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    # Retrieve Phi data
    maxPhi = alldata['algo_data']['maxPhi']
    argmax_constr = alldata['algo_data']['argmax_constr']
    argmax_zsign = alldata['algo_data']['argmax_zsign']
    argmax_zvar = alldata['algo_data']['argmax_zvar']
    argmax_coeff = alldata['algo_data']['argmax_coeff']
    argmax_phis = alldata['algo_data']['argmax_phis']

    # Compute and set cut weights
    sum_exp = 0.0
    for _, phi in argmax_phis.items():
        sum_exp += math.exp(alpha * phi)
    for feat_name, phi in argmax_phis.items():
        nonzero_cutweights.add((cutnum, feat_name))
        cutweights[(cutnum, feat_name)] = math.exp(alpha * phi) / sum_exp

    # Retrieve coefficient data for each nonzero feature
    for feat_name, phi in argmax_phis.items():
        constraint_data = all_constr_data[feat_name]
        sense = constraint_data['sense']

        # Get phi scale value
        phi_scale = 1.0
        if alldata['algo_data']['phi_scale'] == 'percent_violation':
            phi_scale = max(constraint_data['RHS'], 1)
        else:  #alldata['algo_data']['phi_scale'] == 'scaled_abs_violation'
            phi_scale = constraint_data['coeff_inf-norm']

        # Set constant (LHS constant - RHS)
        nonzero_phiConstWeights.add((cutnum, feat_name))
        phiConstWeights[(cutnum, feat_name)] = (constraint_data['constant'] - constraint_data['RHS']) / phi_scale

        # Set linear coefficients
        for var, coeff in constraint_data['lin_terms'].items():
            var_idx = variables[var]
            nonzero_phiLinWeights.add((cutnum, feat_name, var_idx))
            print("Defining weight (%d, %s, %d)"%(cutnum, feat_name, var_idx))
            phiLinWeights[(cutnum, feat_name, var_idx)] = coeff / phi_scale

        # Set quadratic coefficients
        for var_tuple, coeff in constraint_data['quad_terms'].items():
            v1, v2 = var_tuple[0], var_tuple[1]
            v1_idx, v2_idx = variables[v1], variables[v2]
            nonzero_phiQuadWeights.add((cutnum, feat_name, v1_idx, v2_idx))
            print("Defining weight (%d, %s, %d, %d)"%(cutnum, feat_name, v1_idx, v2_idx))
            phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] = coeff / phi_scale

        # Check if phi minus constraint is necessary and swap all signs for >= features
        if sense == '=':
            # phi is absolute value so DO need a minus constraint
            phiMinusToggle[(cutnum, feat_name)] = 1
        else:  # feature is inequality
            # phi is plus operator so DO NOT need a minus constraint
            phiMinusToggle[(cutnum, feat_name)] = 0
            if sense == '>':
                # Violations are reversed so swap sign
                phiConstWeights[(cutnum, feat_name)] *= -1
                for var in constraint_data['lin_terms']:
                    var_idx = variables[var]
                    phiLinWeights[(cutnum, feat_name, var_idx)] *= -1
                for var_tuple in constraint_data['quad_terms']:
                    v1, v2 = var_tuple[0], var_tuple[1]
                    v1_idx, v2_idx = variables[v1], variables[v2]
                    phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] *= -1

    # Scale argmax_zvar terms by error
    for feat_name, terms_list in structure['risky_coeffs'][argmax_coeff]['instances'].items():
        for term_data in terms_list:
            degree, var_data = term_data[0], term_data[1]

            if degree == 'linear':
                var = var_data
                var_idx = variables[var]
                phiLinWeights[(cutnum, feat_name, var_idx)] *= 1 + argmax_zsign * budget

            else:  #degree = 'quad'
                v1, v2 = var_data[0], var_data[1]
                v1_idx, v2_idx = variables[v1], variables[v2]
                phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] *= 1 + argmax_zsign * budget

    log.joint("Adding greedy cut\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: ampl_test.py modfile cutfile')

    alldata = {}
    log = alldata['log'] = danoLogger('ampl_test.log')
    alldata['loud'] = True

    # Get files from arguments
    alldata['MODFILE'] = sys.argv[1]
    alldata['CUTFILE'] = 'cutsrun.dat' if len(sys.argv) == 2 else sys.argv[2]

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

    # Solve and get next iterate solution xt
    solve(alldata)
    breakexit('Done solving problem')

