###############################################################################
# Functions for initializing all data necessary for SOFTMAX_-ADVERSARIAL.
#
# Blake Sisson mbs2246@columbia.edu
# 10/20/2026
###############################################################################
from amplpy import AMPL
from drsk_utils import breakexit
from drsk_versioner import stateversion
from drsk_filemanager import read_config, read_instancefile, drsk_read_paramfile, drsk_read_solfile, drsk_write_cutfile, drsk_read_cutfile, drsk_write_alldata
from drsk_ampl import drsk_read_model, drsk_readandstore_model, drsk_init_cuts
from drsk_gurobi import drsk_store_model
from drsk_algo import drsk_algoLoop
from drsk_separation import drsk_addMultiCuts_Greedy, drsk_addMultiCuts_quasiGreedy


def drsk_read_config(log, filename):
    return read_config(log, filename)
def drsk_read_instancefile(log, filename):
    return read_instancefile(log, filename)


def drsk_initialize(logger, param_file, mod_file, lp_file, sol_file, cut_file_in, cut_file_out, param_override_dict=None):
    alldata = {}
    log = alldata['log'] = logger
    log.joint("Initializing all data...\n")

    alldata['MODFILE'] = mod_file
    log.joint("MODFILE %s\n"%alldata['MODFILE'])
    alldata['LPFILE'] = lp_file
    log.joint("LPFILE %s\n"%alldata['LPFILE'])
    alldata['SOLFILE'] = sol_file
    log.joint("SOLFILE %s\n"%alldata['SOLFILE'])
    alldata['CUTFILE_in'] = cut_file_in
    log.joint("CUTFILE_in %s\n"%alldata['CUTFILE_in'])
    alldata['CUTFILE_out'] = cut_file_out
    log.joint("CUTFILE_out %s\n"%alldata['CUTFILE_out'])
    alldata['PARAMFILE'] = param_file
    log.joint("PARAMFILE %s\n"%alldata['PARAMFILE'])

    # Read parameters
    if param_override_dict:
        params = param_override_dict  # Use dictionary passed
    else:
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
    alldata['prob_data']['variables'] = {}             # Dictionary: variable name --> variable index (exluding artifical and dummy)
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
    alldata['struct_data']['features'] = []                                         # List of features, i.e., constraint with risky coefficients
    alldata['struct_data']["risky_coeffs"] = {}                                     # Dictionary: coefficient --> coefficient data (index, zvar, instances)
    alldata['struct_data']['num_unique'] = 0                                        # Number of unique risky coefficients
    alldata['struct_data']['budget'] = params['budget']                             # Constraint error budget
    alldata['struct_data']['decimal_risk_thresh'] = params['decimal_risk_thresh']   # Number of decimal places coefficients need to be considered risky

    # Initialize cut data  #TODO populate dicts from cut file
    alldata['cut_data'] = {}                                # All cut related data stored here
    alldata['cut_data']['maxcuts'] = params['maxcuts']      # Maximum number of cuts
    alldata['cut_data']['ncuts_add'] = params['ncuts_add']  # Number of cuts to add to Master per iteration of algorithm
    alldata['cut_data']['cut_phiThresh'] = params['cut_phiThresh']  # Cuts whose corresponding phi max is below this percent of maxPhi are deemed insignificant
    alldata['cut_data']['numcuts'] = 0                      # Number of cuts to use in solve
    alldata['cut_data']['nonzero_cutweights'] = set()       # Set: (cut number, feat name) pairs with nonzero weight
    alldata['cut_data']['cutweights'] = {}                  # Dict: (cut number, feat name) --> weight
    alldata['cut_data']['nonzero_phiQuadWeights'] = set()   # Set: (cut number, feat name, var idx, var idx) tuples with nonzero weight
    alldata['cut_data']['phiQuadWeights'] = {}              # Quadratic weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var idx, var idx) --> coefficient * (1 + z)
    alldata['cut_data']['nonzero_phiLinWeights'] = set()    # Set: (cut number, feat name, var idx) tuples with nonzero weight
    alldata['cut_data']['phiLinWeights'] = {}               # Linear weights defining phi_i(.|z) for each cut. Dict: (cut number, feat name, var idx) --> coefficient * (1 + z)
    alldata['cut_data']['phiConstWeights'] = {}             # Constants defining phi_i(.|z). Dict: (cut number, feature name) --> constant
    alldata['cut_data']['phiMinusToggle'] = {}              # Toggle for whether the minus constraint is needed in phi definition for this cut and feature. Dict: (cut number, feat name, var) --> 0/1
    if params['cut_method'] == 'greedy':                    # Define cut method to use
        alldata['cut_data']['cut_method'] = drsk_addMultiCuts_Greedy
    elif params['cut_method'] == 'quasi-greedy':
        alldata['cut_data']['cut_method'] = drsk_addMultiCuts_quasiGreedy
    else:
        log.joint("Invalid cut type %s\n"%params['cut_type'])

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
    alldata['algo_data']['solve_time_limit'] = params['solve_time_limit']  # Maximum solver time limit, if reached the algorithm exits
    alldata['algo_data']['soln_provided'] = 0                 # Whether an initial solution is provided
    alldata['algo_data']['all_phi_data'] = {}                 # Save phi data for each z variable. Dict: zvar name --> (dictionary: maxPhi, argmax_feat, argmax_zsign, coeff)
                                                              #                                          'sorted_zvars' --> list of zvars sorted by corresponding maxphi in descending order

    # Initialize solver
    ampl = alldata['algo_data']['ampl']
    solver = alldata['algo_data']['solver']
    timelimit = alldata['algo_data']['solve_time_limit']
    ampl.setOption('solver', solver)
    log.joint("Using solver: %s\n"%solver)
    # Gurobi specific options
    ampl.set_option('gurobi_auxfiles', "rc")
    sol_cmd = 'solutionlimit=2'
    out_cmd = 'outlev=1'
    time_cmd = 'timelimit=' + str(timelimit)
    file_cmd = 'writeprob=models/model_' + str(alldata['algo_data']['iteration']) + '.lp'
    ampl.set_option('gurobi_options', sol_cmd + ' ' + out_cmd + ' ' + time_cmd + ' ' + file_cmd)
    # Tell Knitro to write model to file
    # file_cmd = 'writeformat=lp writefile=models/model_' + str(alldata['algo_data']['iteration']) + '.lp'
    # ampl.set_option("knitro_options", file_cmd)

    log.joint("Done initializing all data.\n")
    return alldata


def drsk_start(logger, param_file, mod_file, lp_file, sol_file, cut_file_in, cut_file_out, param_override_dict=None):
    logger.joint("Start drsk program.\n")
    stateversion(logger)

    # Initialize problem data 
    alldata = drsk_initialize(logger, param_file, mod_file, lp_file, sol_file, cut_file_in, cut_file_out, param_override_dict)
    if alldata['breakpoints']: breakexit('Done initializing all data')

    # If no lp file, use AMPL to parse
    if lp_file == 'NONE':
        # Read problem into AMPL and store problem data and risk structure
        drsk_readandstore_model(alldata)

    # If lp file provided, use Gurobi to parse
    else:
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

    # Initialize solution if a sol file is provided
    if sol_file != 'NONE':
        objval, input_dict = drsk_read_solfile(logger, alldata['SOLFILE'])
        alldata['algo_data']['soln_provided'] = 1

        # Initialize all variables to zero then overwrite those from the solution file
        alldata['algo_data']['soln_vector_dict'] = {varname: 0.0 for varname in alldata['prob_data']['variables']}
        alldata['algo_data']['soln_vector_dict'].update(input_dict)

        alldata['algo_data']['cost'] = objval
        alldata['algo_data']['Phi_L'] = 0

    # Run algorithm
    result_str = drsk_algoLoop(alldata)

    # Write cut file
    drsk_write_cutfile(alldata, cut_file_out)

    # Result result string
    logger.joint("Finished drsk program.\n")
    return result_str


    