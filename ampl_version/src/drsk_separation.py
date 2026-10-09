###############################################################################
# Functions for computing the separation step of the SOFTMAX-ADVERSARIAL 
# algorithm.
#
# Blake Sisson mbs2246@columbia.edu
# 10/7/2026
###############################################################################
import math

def addCut_greedy(alldata):
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
    argmax_feat = alldata['algo_data']['argmax_feat']
    argmax_zsign = alldata['algo_data']['argmax_zsign']
    argmax_zvar = alldata['algo_data']['argmax_zvar']
    argmax_coeff = alldata['algo_data']['argmax_coeff']
    argmax_phis = alldata['algo_data']['argmax_phis']

    # 1. Set cut weights
    nonzero_cutweights.add((cutnum, argmax_feat))
    cutweights[(cutnum, argmax_feat)] = 1
    log.joint("Cut #%d (feature weight):\n"%cutnum)
    log.joint("  %s  %g\n"%(argmax_feat, 1))

    # 2. Define phi...

    # Get constraint data of argmax feature
    constraint_data = all_constr_data[argmax_feat]
    sense = constraint_data['sense']

    # Get phi scale value
    phi_scale = 1.0
    if alldata['algo_data']['phi_scale'] == 'percent_violation':
        phi_scale = max(constraint_data['RHS'], 1)
    else:  #alldata['algo_data']['phi_scale'] == 'scaled_abs_violation'
        phi_scale = constraint_data['coeff_inf-norm']

    # Set constant (LHS constant - RHS)
    nonzero_phiConstWeights.add((cutnum, argmax_feat))
    phiConstWeights[(cutnum, argmax_feat)] = (constraint_data['constant'] - constraint_data['RHS']) / phi_scale
    if loud: log.joint(" - Defining constant (%d, %s)\n"%(cutnum, argmax_feat))

    # Set linear coefficients
    for var, coeff in constraint_data['lin_terms'].items():
        var_idx = variables[var]
        nonzero_phiLinWeights.add((cutnum, argmax_feat, var_idx))
        phiLinWeights[(cutnum, argmax_feat, var_idx)] = coeff / phi_scale
        if loud: log.joint(" - Defining weight (%d, %s, %d)\n"%(cutnum, argmax_feat, var_idx))

    # Set quadratic coefficients
    for var_tuple, coeff in constraint_data['quad_terms'].items():
        v1, v2 = var_tuple[0], var_tuple[1]
        v1_idx, v2_idx = variables[v1], variables[v2]
        nonzero_phiQuadWeights.add((cutnum, argmax_feat, v1_idx, v2_idx))
        phiQuadWeights[(cutnum, argmax_feat, v1_idx, v2_idx)] = coeff / phi_scale
        if loud: log.joint(" - Defining weight (%d, %s, %d, %d)\n"%(cutnum, argmax_feat, v1_idx, v2_idx))

    # Check if phi minus constraint is necessary and swap all signs for >= features
    if sense == '=':
        # phi is absolute value so DO need a minus constraint
        phiMinusToggle[(cutnum, argmax_feat)] = 1
    else:  # feature is inequality
        # phi is plus operator so DO NOT need a minus constraint
        phiMinusToggle[(cutnum, argmax_feat)] = 0
        if sense == '>':
            # Violations are reversed so swap sign
            phiConstWeights[(cutnum, argmax_feat)] *= -1
            for var in constraint_data['lin_terms']:
                var_idx = variables[var]
                phiLinWeights[(cutnum, argmax_feat, var_idx)] *= -1
            for var_tuple in constraint_data['quad_terms']:
                v1, v2 = var_tuple[0], var_tuple[1]
                v1_idx, v2_idx = variables[v1], variables[v2]
                phiQuadWeights[(cutnum, argmax_feat, v1_idx, v2_idx)] *= -1

    # Scale argmax_zvar terms by error
    terms_list = structure['risky_coeffs'][argmax_coeff]['instances'][argmax_feat]
    for term_data in terms_list:
        degree, var_data = term_data[0], term_data[1]

        if degree == 'linear':
            var = var_data
            var_idx = variables[var]
            phiLinWeights[(cutnum, argmax_feat, var_idx)] *= 1 + argmax_zsign * budget

        else:  #degree = 'quad'
            v1, v2 = var_data[0], var_data[1]
            v1_idx, v2_idx = variables[v1], variables[v2]
            phiQuadWeights[(cutnum, argmax_feat, v1_idx, v2_idx)] *= 1 + argmax_zsign * budget

    log.joint("Added cut using Greedy\n")


def addCut_quasiGreedy(alldata):
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
    argmax_feat = alldata['algo_data']['argmax_feat']
    argmax_zsign = alldata['algo_data']['argmax_zsign']
    argmax_zvar = alldata['algo_data']['argmax_zvar']
    argmax_coeff = alldata['algo_data']['argmax_coeff']
    argmax_phis = alldata['algo_data']['argmax_phis']

    # 1. Compute and set cut weights
    sum_exp = 0.0
    for phi in argmax_phis.values():
        sum_exp += math.exp(alpha * phi)
    log.joint("Cut #%d (feature weight):\n"%cutnum)
    for feat_name, phi in argmax_phis.items():
        nonzero_cutweights.add((cutnum, feat_name))
        weight = math.exp(alpha * phi) / sum_exp
        cutweights[(cutnum, feat_name)] = weight
        log.joint("  %s  %g\n"%(feat_name, weight))

    # 2. Define phi constraints

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
        if loud: log.joint(" - Defining constant (%d, %s)\n"%(cutnum, feat_name))

        # Set linear coefficients
        for var, coeff in constraint_data['lin_terms'].items():
            var_idx = variables[var]
            nonzero_phiLinWeights.add((cutnum, feat_name, var_idx))
            phiLinWeights[(cutnum, feat_name, var_idx)] = coeff / phi_scale
            if loud: log.joint(" - Defining weight (%d, %s, %d)\n"%(cutnum, feat_name, var_idx))

        # Set quadratic coefficients
        for var_tuple, coeff in constraint_data['quad_terms'].items():
            v1, v2 = var_tuple[0], var_tuple[1]
            v1_idx, v2_idx = variables[v1], variables[v2]
            nonzero_phiQuadWeights.add((cutnum, feat_name, v1_idx, v2_idx))
            phiQuadWeights[(cutnum, feat_name, v1_idx, v2_idx)] = coeff / phi_scale
            if loud: log.joint(" - Defining weight (%d, %s, %d, %d)\n"%(cutnum, feat_name, v1_idx, v2_idx))

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

    log.joint("Added cut using Quasi-Greedy\n\n")