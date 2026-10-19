###############################################################################
# Functions for initializing all data necessary for SOFTMAX_-ADVERSARIAL.
#
# Blake Sisson mbs2246@columbia.edu
# 10/13/2026
###############################################################################
from amplpy import AMPL
from myutils import breakexit
from drsk_filemanager import drsk_read_paramfile, drsk_write_cutfile, drsk_read_cutfile, drsk_write_alldata
from drsk_ampl import drsk_read_model, drsk_readandstore_model, drsk_init_cuts
from drsk_gurobi import drsk_store_model
from drsk_algo import drsk_algoLoop


def drsk_initialize(logger, param_file, mod_file, lp_file, cut_file_in, cut_file_out):
    alldata = {}
    log = alldata['log'] = logger

    alldata['MODFILE'] = mod_file
    log.joint("MODFILE %s\n"%alldata['MODFILE'])
    alldata['LPFILE'] = lp_file
    log.joint("LPFILE %s\n"%alldata['LPFILE'])
    alldata['CUTFILE_in'] = cut_file_in
    log.joint("CUTFILE_in %s\n"%alldata['CUTFILE_in'])
    alldata['CUTFILE_out'] = cut_file_out
    log.joint("CUTFILE_out %s\n"%alldata['CUTFILE_out'])
    alldata['PARAMFILE'] = param_file
    log.joint("PARAMFILE %s\n"%alldata['PARAMFILE'])

    # Read parameters
    params = drsk_read_paramfile(log, alldata['PARAMFILE'])

    # Set log output levels
    alldata['loud'] = params['loud']
    alldata['verbose'] = params['verbose']
    alldata['breakpoints'] = params['breakpoints']

    # Initialize prob data
    alldata['prob_data'] = {}                          # All problem related data stored here
    alldata['prob_data']['lam_hi'] = params['lam_hi']  # Lambda hi parameter for choosing Theta automatically
    alldata['prob_data']['lam_lo'] = params['lam_lo']  # Lambda hi parameter for choosing Theta automatically
    alldata['prob_data']['xi'] = params['xi']          # Xi parameter for choosing Theta automatically
    alldata['prob_data']['constraints'] = []           # List of all constraints
    alldata['prob_data']['variables'] = {}             # Dictionary: variable name --> variable index (exluding artifical and dummy
    alldata['prob_data']['all_constr_data'] = {}       # Dictionary: constraint name --> constraint data
    alldata['prob_data']['gurobimodel'] = None         # Gurobi object
    if params['theta'] == 'auto':                      # Theta is to be set automatically
        alldata['prob_data']['autoTheta'] = 1          
        alldata['prob_data']['Theta'] = 0.0
    else:                                              # Theta is to set to value provided
        alldata['prob_data']['autoTheta'] = 0
        alldata['prob_data']['Theta'] = float(params['theta'])

    # Initialize coefficient risk structure
    alldata['struct_data'] = {}                                                     # All risky coefficient structure data stored here
    alldata['struct_data']["numfeats"] = 0                                          # Number of features (constraints with risky coefficients)
    alldata['struct_data']['features'] = []                                           # List of features, i.e., constraint with risky coefficients
    alldata['struct_data']["risky_coeffs"] = {}                                     # Dictionary: coefficient --> coefficient data (index, zvar, instances)
    alldata['struct_data']['num_unique'] = 0                                        # Number of unique risky coefficients
    alldata['struct_data']['budget'] = params['budget']                             # Constraint error budget
    alldata['struct_data']['decimal_risk_thresh'] = params['decimal_risk_thresh']   # Number of decimal places coefficients need to be considered risky

    # Initialize cut data  #TODO populate dicts from cut file
    alldata['cut_data'] = {}                                # All cut related data stored here
    alldata['cut_data']['maxcuts'] = params['maxcuts']      # Maximum number of cuts
    alldata['cut_data']['numcuts'] = 0                      # Number of cuts to use in solve
    alldata['cut_data']['nonzero_cutweights'] = set()       # Set: (cut number, feat name) pairs with nonzero weight
    alldata['cut_data']['cutweights'] = {}                  # Dict: (cut number, feat name) --> weight
    alldata['cut_data']['nonzero_phiQuadWeights'] = set()   # Set: (cut number, feat name, var idx, var idx) tuples with nonzero weight
    alldata['cut_data']['phiQuadWeights'] = {}              # Quadratic weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var idx, var idx) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiLinWeights'] = set()    # Set: (cut number, feat name, var idx) tuples with nonzero weight
    alldata['cut_data']['phiLinWeights'] = {}               # Linear weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var idx) --> coefficient * (1 + z)
    alldata['cut_data']['phiConstWeights'] = {}             # Constants defining phi_i(.|z). Dict: (cut number, feature name) --> constant
    alldata['cut_data']['phiMinusToggle'] = {}              # Toggle for whether the minus constraint is needed in phi definition for this cut and feature. Dict: (cut number, feat name, var) --> 0/1

    # Initialize algorithm data (Note: extra greedy specific algo data defined in greedy Phi method)
    alldata['algo_data'] = {}                                 # All algorithm related data stored here
    alldata['algo_data']['ampl'] = AMPL()                     # AMPL object  
    alldata['algo_data']['alpha'] = params['alpha']           # alpha value (for softmax)
    alldata['algo_data']['phi_scale'] = params['phi_scale']   # phi scale value, for scaling phi
    alldata['algo_data']['solver'] = params['solver']         # Solver to use
    alldata['algo_data']['soln_vector_dict'] = {}             # Solution dctionary: variable name --> value
    alldata['algo_data']['Phi_L'] = 0.0                       # Phi_L variable value
    alldata['algo_data']['cost'] = 0.0                        # Cost value in objective
    alldata['algo_data']['iteration'] = 0                     # Iteration number
    alldata['algo_data']['tol'] = params['tol']               # Relative convergence tolerance
    alldata['algo_data']['maxits'] = params['maxits']         # Maximum number of iterations
    alldata['algo_data']['PhiReduc'] = params['PhiReduc']     # Percent Phi reduction for early convergence
    alldata['algo_data']['zerothresh'] = params['zerothresh'] # Tolerance for float to be considered zero

    return alldata


def drsk_start(logger, param_file, mod_file, lp_file, cut_file_in, cut_file_out):
    # Initialize problem data 
    alldata = drsk_initialize(logger, param_file, mod_file, lp_file, cut_file_in, cut_file_out)
    if alldata['breakpoints']: breakexit('Done initializing all data')

    if lp_file == 'NONE':  # If no lp file, use AMPL to parse
        # Read problem into AMPL and store problem data and risk structure
        drsk_readandstore_model(alldata)

    else:  # If lp file provided, use Gurobi to parse
        # Read problem into AMPL
        drsk_read_model(alldata)
        if alldata['breakpoints']: breakexit('Done reading problem')

        # Store problem data and risk structure
        drsk_store_model(alldata)
        if alldata['breakpoints']: breakexit('Done parsing problem')

    # Add cut placeholders to AMPL model
    drsk_init_cuts(alldata)
    if alldata['breakpoints']: breakexit('Done adding cuts placeholders to model')

    # Writing alldata to file, for debugging
    drsk_write_alldata(alldata, "alldata.json")

    # Run algorithm
    result_str = drsk_algoLoop(alldata)

    # Write cut file
    drsk_write_cutfile(alldata, cut_file_out)

    # Result result string
    return result_str


    