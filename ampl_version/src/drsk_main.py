###############################################################################
# Functions for initializing all data necessary for SOFTMAX_-ADVERSARIAL.
#
# Blake Sisson mbs2246@columbia.edu
# 10/13/2026
###############################################################################
import json
from pathlib import Path
import shutil
from amplpy import AMPL
from myutils import breakexit
from cutfilereader import write_cutfile, read_cutfile
from drsk_ampl import drsk_read, drsk_read_and_store, drsk_init_cuts
from drsk_lp import drsk_storelp
from drsk_algo import drsk_algoLoop


def read_config(log, filename):
    '''Read settings from configuration file'''
    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    config_data = {}
    paramfile = 'NONE'
    modfile = 'NONE'
    lpfile = 'NONE'
    cutfile_in = 'NONE'
    cutfile_out = 'NONE'
    instance_file = 'NONE'

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'PARAMFILE':
                paramfile = thisline[1]
            elif word == 'MODFILE':
                modfile = thisline[1]
            elif word == 'LPFILE':
                lpfile = thisline[1]
            elif word == 'CUTFILE':
                type = thisline[1]
                if type == 'in':
                    cutfile_in = thisline[2]
                elif type == 'out':
                    cutfile_out = thisline[2]
            elif word == 'INSTANCE_FILE':
                instance_file = thisline[1]
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + "\n")

        linenum += 1

    for x in [('PARAMFILE', paramfile),
              ('MODFILE', modfile),
              ('LPFILE', lpfile),
              ('CUTFILE_in', cutfile_in),
              ('CUTFILE_out', cutfile_out),
              ('INSTANCE_FILE', instance_file)]:
        config_data[x[0]] = x[1]

    return config_data


def parse_instance_file(log, instance_file):
    '''Read instances from file and return list of ids'''
    try:
        f = open(instance_file, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + instance_file + "\n")

    instance_ids = []

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]
            if word == 'END':
                break
            instance_ids.append(word)
        linenum += 1

    return instance_ids


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
    maxcuts = 10
    tol = 'None'
    maxits = 'None'
    PhiReduc = 'None'
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
            elif word == 'maxcuts':
                maxcuts = float(thisline[1])
            elif word == 'tol':
                tol = float(thisline[1])
            elif word == 'maxits':
                maxits = int(thisline[1])
            elif word == 'PhiReduc':
                PhiReduc = float(thisline[1])
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
              ('maxcuts', maxcuts),
              ('tol', tol),
              ('maxits', maxits),
              ('PhiReduc', PhiReduc),
              ('loud', loud),
              ('verbose', verbose),
              ('breakpoints', breakpoints)]:
        if x[1] == 'NONE':
            log.stateandquit(' no ' + x[0] + ' input'+'\n')
        params[x[0]] = x[1]
        log.joint(x[0] + ' ' + str(x[1])+ '\n')

    return params


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
    params = drsk_readparameters(log, alldata['PARAMFILE'])

    # Set log output levels
    alldata['loud'] = params['loud']
    alldata['verbose'] = params['verbose']
    alldata['breakpoints'] = params['breakpoints']

    # Initialize prob data
    alldata['prob_data'] = {}                        # All problem related data stored here
    alldata['prob_data']['Theta'] = params['theta']  # Theta value for weighted objective parameter
    alldata['prob_data']['constraints'] = []         # List of all constraints
    alldata['prob_data']['variables'] = {}           # Dictionary: variable name --> variable index (exluding artifical and dummy
    alldata['prob_data']['all_constr_data'] = {}     # Dictionary: constraint name --> constraint data
    alldata['prob_data']['gurobimodel'] = None

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
    alldata['algo_data']['PhiReduc'] = params['PhiReduc']   # Percent Phi reduction for early convergence

    return alldata


def drsk_start(logger, param_file, mod_file, lp_file, cut_file_in, cut_file_out):
    # Initialize problem data 
    alldata = drsk_initialize(logger, param_file, mod_file, lp_file, cut_file_in, cut_file_out)
    if alldata['breakpoints']: breakexit('Done initializing all data')

    if lp_file == 'NONE':  # If no lp file, use AMPL to parse
        # Read problem into AMPL and store problem data and risk structure
        drsk_read_and_store(alldata)

    else:  # If lp file provided, use Gurobi to parse
        # Read problem into AMPL
        drsk_read(alldata)
        if alldata['breakpoints']: breakexit('Done reading problem')

        # Store problem data and risk structure
        drsk_storelp(alldata)
        if alldata['breakpoints']: breakexit('Done parsing problem')

    # Add cut placeholders to AMPL model
    drsk_init_cuts(alldata)
    if alldata['breakpoints']: breakexit('Done adding cuts placeholders to model')

    # Writing alldata to file, for debugging
    # def is_serializable(value):
    #     try:
    #         json.dumps(value)
    #         return True
    #     except TypeError:
    #         return False
    # clean_data = {k: v for k, v in alldata.items() if is_serializable(v)}
    # with open("alldata.json", "w", encoding="utf-8") as f:
    #     json.dump(
    #         clean_data, 
    #         f, 
    #         indent=4,          # Adds 4 spaces of indentation
    #         sort_keys=True,     # Sorts the dictionary keys alphabetically
    #         ensure_ascii=False  # Keeps non-English/Unicode text intact
    #     )
    # if alldata['breakpoints']: breakexit('Saved all data to file')

    # Run algorithm
    result_str = drsk_algoLoop(alldata)

    # Write cut file
    write_cutfile(alldata, cut_file_out)

    # Result result string
    return result_str


    