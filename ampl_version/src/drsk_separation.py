###############################################################################
# Functions for computing the separation step of the SOFTMAX-ADVERSARIAL 
# algorithm.
#
# Blake Sisson mbs2246@columbia.edu
# 10/7/2026
###############################################################################
import math

def get_phi_scale(alldata, log, constraint_data):
    phi_scale = 1.0

    if alldata['algo_data']['phi_scale'] == 'percent_violation':
        phi_scale = max(constraint_data['RHS'], 1.0)
    elif alldata['algo_data']['phi_scale'] == 'scaled_abs_violation':
        phi_scale = constraint_data['coeff_inf-norm']
    else:
        log.joint('ERROR: invalid phi_scale: %s\n'%(phi_scale))

    return phi_scale


def define_phi_constraints(alldata, cutnum, feat_name, argmax_coeff, argmax_zsign):
    '''Add constraints defining phi for the given feature (feat_name) and z variable (determined by coeff and zsign)'''
    log = alldata['log']
    loud = alldata['loud']
    verbose = alldata['verbose']
    all_constr_data = alldata['prob_data']['all_constr_data']
    variables = alldata['prob_data']['variables']
    structure = alldata['struct_data']
    budget = structure['budget']

    # Retrieve cut data memory
    nonzero_phiQuadWeights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    constraint_data = all_constr_data[feat_name]
    sense = constraint_data['sense']

    # Get phi scale value
    phi_scale = get_phi_scale(alldata, log, constraint_data)

    # Set constant (LHS constant - RHS)
    phiConstWeights[(cutnum, feat_name)] = (constraint_data['constant'] - constraint_data['RHS']) / phi_scale
    if loud: log.joint(" - Defining constant (%d, %s)\n"%(cutnum, feat_name))
    if verbose: log.joint("DEBUG: + constant - rhs = %g - %g\n"%(constraint_data['constant'], constraint_data['RHS']))

    # Set linear coefficients
    for var, _coeff in constraint_data['lin_terms'].items():
        var_idx = variables[var]
        nonzero_phiLinWeights.add((cutnum, feat_name, var_idx))
        phiLinWeights[(cutnum, feat_name, var_idx)] = _coeff / phi_scale
        if loud: log.joint(" - Defining weight (%d, %s, %d)\n"%(cutnum, feat_name, var_idx))
        if verbose: log.joint("DEBUG: + %g * %s\n"%(_coeff, var))

    # Set quadratic coefficients
    for var_tuple, _coeff in constraint_data['quad_terms'].items():
        v1, v2 = var_tuple[0], var_tuple[1]
        v1_idx, v2_idx = variables[v1], variables[v2]
        nonzero_phiQuadWeights.add((cutnum, feat_name, v1_idx, v2_idx))
        phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] = _coeff / phi_scale
        if loud: log.joint(" - Defining weight (%d, %s, %d, %d)\n"%(cutnum, feat_name, v1_idx, v2_idx))
        if verbose: log.joint("DEBUG: + %g * %s * %s\n"%(_coeff, v1, v2))

    # Check if phi minus constraint is necessary and swap all signs for >= features
    if sense == '=':
        # phi is absolute value so DO need a minus constraint
        phiMinusToggle[(cutnum, feat_name)] = 1
        if verbose: log.joint("DEBUG: feature is equality, add phi Minus constraint\n")
    else:  # feature is inequality
        # phi is plus operator so DO NOT need a minus constraint
        phiMinusToggle[(cutnum, feat_name)] = 0
        if verbose: log.joint("DEBUG: feature is inequality, no phi Minus constraint\n")
        if sense == '>=' or sense == '>':
            # Violations are reversed so swap sign
            phiConstWeights[(cutnum, feat_name)] *= -1
            for var in constraint_data['lin_terms']:
                var_idx = variables[var]
                phiLinWeights[(cutnum, feat_name, var_idx)] *= -1
            for var_tuple in constraint_data['quad_terms']:
                v1, v2 = var_tuple[0], var_tuple[1]
                v1_idx, v2_idx = variables[v1], variables[v2]
                phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] *= -1
            if verbose: log.joint("DEBUG: feature is >= ineq, negate all data\n")

    # Scale zvar terms by error
    terms_list = structure['risky_coeffs'][argmax_coeff]['instances'][feat_name]
    for degree, var_data, sign in terms_list:
        if degree == 'linear':
            var = var_data
            var_idx = variables[var]
            phiLinWeights[(cutnum, feat_name, var_idx)] *= 1 + argmax_zsign * budget
            if verbose: log.joint("DEBUG: %d * %g * %s term gets (1 + %g)\n"%(sign, argmax_coeff, var, argmax_zsign * budget))

        else:  #degree = 'quad'
            v1, v2 = var_data[0], var_data[1]
            v1_idx, v2_idx = variables[v1], variables[v2]
            phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] *= 1 + argmax_zsign * budget
            if verbose: log.joint("DEBUG: %d * %g * %s * %s term gets (1 + %g)\n"%(sign, argmax_coeff, v1, v2, argmax_zsign * budget))


def drsk_addCut_greedy(alldata, argmax_feat, argmax_coeff, argmax_zsign):
    log = alldata['log']

    # Increment cut number
    alldata['cut_data']['numcuts'] += 1

    # Retrieve cut data to add new cut to
    cutnum = alldata['cut_data']['numcuts']
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']

    # 1. Set cut weights
    nonzero_cutweights.add((cutnum, argmax_feat))
    cutweights[(cutnum, argmax_feat)] = 1
    log.joint("Cut #%d (feature weight):\n"%cutnum)
    log.joint("  %s  %g\n"%(argmax_feat, 1))

    # 2. Define phi constraints
    define_phi_constraints(alldata, cutnum, argmax_feat, argmax_coeff, argmax_zsign)

    log.joint("Added cut using Greedy\n")


def drsk_addCut_quasiGreedy(alldata, phis, argmax_coeff, argmax_zsign):
    log = alldata['log']

    # Increment cut number
    alldata['cut_data']['numcuts'] += 1

    # Retrieve cut data to add new cut to
    cutnum = alldata['cut_data']['numcuts']
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']

    # 1. Compute and set cut weights
    alpha = alldata['algo_data']['alpha']
    sum_exp = 0.0
    for phi in phis.values():
        sum_exp += math.exp(alpha * phi)
    log.joint("Cut #%d (feature weight):\n"%cutnum)
    for feat_name, phi in phis.items():
        nonzero_cutweights.add((cutnum, feat_name))
        weight = math.exp(alpha * phi) / sum_exp
        cutweights[(cutnum, feat_name)] = weight
        log.joint("  %s  %g\n"%(feat_name, weight))

    # 2. Define phi constraints, for each nonzero feature
    for feat_name in phis:
        define_phi_constraints(alldata, cutnum, feat_name, argmax_coeff, argmax_zsign)

    log.joint("Added cut using Quasi-Greedy\n")


def drsk_addMultiCuts_Greedy(alldata):
    log = alldata['log']
    loud = alldata['loud']
    log.joint("Adding multiple Greedy cuts...\n")

    # Get phi data
    all_phi_data = alldata['algo_data']['all_phi_data']

    # Get sorted zvars
    sorted_zvars = all_phi_data['sorted_zvars']

    # Store maxPhi, to ignore insignificant cuts
    maxPhi = all_phi_data[sorted_zvars[0]]['maxPhi']

    # Cuts whose corresponding phi max is below this percent of maxPhi are deemed insignificant and not added
    phiThresh_percent = alldata['cut_data']['cut_phiThresh']

    count = 0
    max_ncuts = min(alldata['cut_data']['ncuts_add'], len(sorted_zvars))
    for i in range(max_ncuts):
        zvar = sorted_zvars[i]
        phi_data = all_phi_data[zvar]

        # Break if max phi of this zvar is too small
        maxPhi_z = phi_data['maxPhi']
        if maxPhi_z < phiThresh_percent * maxPhi:
            if loud: log.joint("  Stop adding cuts: maxPhi_z = %g < %g = %g * %g = phiThresh_percent * maxPhi\n"%(maxPhi_z, phiThresh_percent * maxPhi, phiThresh_percent, maxPhi))
            break
        
        # Get phi data
        argmax_feat_z = phi_data['argmax_feat']
        coeff = phi_data['coeff']
        argmax_zsign_z = phi_data['argmax_zsign']

        count += 1
        log.joint("Adding greedy cut for zvar=%s coeff=%g with phi=%g\n"%(zvar, coeff, maxPhi_z))
        drsk_addCut_greedy(alldata, argmax_feat_z, coeff, argmax_zsign_z)

    log.joint("Done adding %d Greedy cuts.\n"%count)


def drsk_addMultiCuts_quasiGreedy(alldata):
    log = alldata['log']
    loud = alldata['loud']
    log.joint("Adding multiple Quasi-Greedy cuts...\n")

    # Get phi data
    all_phi_data = alldata['algo_data']['all_phi_data']

    # Get sorted zvars
    sorted_zvars = all_phi_data['sorted_zvars']

    # Store maxPhi, to ignore insignificant cuts
    maxPhi = all_phi_data[sorted_zvars[0]]['maxPhi']

    # Cuts whose corresponding phi max is below this percent of maxPhi are deemed insignificant and not added
    phiThresh_percent = alldata['cut_data']['cut_phiThresh']

    count = 0
    max_ncuts = min(alldata['cut_data']['ncuts_add'], len(sorted_zvars))
    for i in range(max_ncuts):
        zvar = sorted_zvars[i]
        phi_data = all_phi_data[zvar]

        # Break if max phi of this zvar is too small
        maxPhi_z = phi_data['maxPhi']
        if maxPhi_z < phiThresh_percent * maxPhi:
            if loud: log.joint("  Stop adding cuts: maxPhi_z = %g < %g = %g * %g = phiThresh_percent * maxPhi\n"%(maxPhi_z, phiThresh_percent * maxPhi, phiThresh_percent, maxPhi))
            break
        
        # Get phi data
        phis = phi_data['phis']
        coeff = phi_data['coeff']
        argmax_zsign_z = phi_data['argmax_zsign']

        count += 1
        log.joint("Adding greedy cut for zvar=%s coeff=%g with phi=%g\n"%(zvar, coeff, maxPhi_z))
        drsk_addCut_quasiGreedy(alldata, phis, coeff, argmax_zsign_z)

    log.joint("Done adding %d Quasi-Greedy cuts.\n"%count)