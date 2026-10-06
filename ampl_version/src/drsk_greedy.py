###############################################################################
# Functions for greedily evaluting Phi at a given solution vector and adding 
# greedy cuts.
#
# Blake Sisson mbs2246@columbia.edu
# 10/6/2026
###############################################################################
import math

def eval_Phi_greedy(alldata, soln_vector_dict):
    log = alldata['log']
    loud = alldata['loud']
    all_constr_data = alldata['prob_data']['all_constr_data']
    structure = alldata['struct_data']
    budget = structure['budget']

    log.joint("Computing Phi using greedy method...\n")

    lhs_dict = {}  # Save lhs values for reused when applicable

    # Running max Phi(x) with corresponding: constraint, z sign, z variable, and coefficient
    maxPhi = 0.0
    argmax_constr = ''
    argmax_zsign = 0
    argmax_zvar = ''
    argmax_coeff = 0.0
    argmax_phis = {}  # phi values for each feature using max greedy zvar, Dict: feat_name --> phi_i(x^t | z^t = greedy(zvar, budget))

    # Also record running max sum phi(x)'s with corresponding: z sign, z varible, and coefficient
    maxsumphi = 0.0
    argmaxsum_zsign_list = 0
    argmaxsum_zvar = ''
    argmaxsum_coeff = 0

    # Loop over all z, i.e., unique risky coefficients
    for coeff, coeff_dict in structure['risky_coeffs'].items():
        # Running max Phi(|z) and correesponding constraint and z sign
        maxPhi_z = 0.0
        argmax_constr_z = ''
        argmax_zsign_z = 0
        argmax_phis_z = {}  # phi values for each feature greedily using this zvar, Dict: feat_name --> phi_i(x^t | z^t = greedy(zvar, budget))

        # Running sum of phi's, i.e., sum of violations
        sumphis = 0.0

        # Also record list of z signs to track changes
        zsign_list = []

        if loud: log.joint("  Coeff %g\n"%(coeff))

        # Loop over all constraints this risky coefficient appears in
        for constr_name, constr_instance_list in coeff_dict['instances'].items():
            constr_dict = all_constr_data[constr_name]
            rhs = constr_dict['RHS']

            # Compute LHS
            lhs = lhs_dict.get(constr_name)
            if not lhs:
                # Constant
                lhs = constr_dict['constant']
                # Linear terms
                for v, c in constr_dict['lin_terms'].items():
                    v_val = soln_vector_dict[v]
                    lhs += c * v_val
                # Quadratic terms
                for v_tuple, c in constr_dict['quad_terms'].items():
                    v1, v2 = v_tuple[0], v_tuple[1]
                    v1_val, v2_val = soln_vector_dict[v1], soln_vector_dict[v2]
                    lhs += c * v1_val * v2_val
                lhs_dict[constr_name] = lhs

            # Compute error term (from setting z = budget, for z corresponding to coeff)
            error_term = 0.0
            for degree, var in constr_instance_list:
                if degree == 'quad':
                    v1, v2 = var[0], var[1]
                    v1_val, v2_val = soln_vector_dict[v1], soln_vector_dict[v2]
                    error_term += v1_val * v2_val
                else:  #linear
                    var_val = soln_vector_dict[var]
                    error_term += var_val
            error_term *= coeff * budget  #save repetitive multiplcation for last

            # Get constraint sense
            sense = constr_dict['sense']

            # Compute slack
            if sense == '>':
                slack = lhs - rhs
            elif sense == '<':
                slack = rhs - lhs
            else:
                slack = 0

            # Compute constraint violation (depends on constraint sense)
            if sense == '=':
                violation = error_term
                zsign = 1 if violation < 0 else -1
            else:  #constr is inequality
                violation = max(0, math.fabs(error_term) - slack)  #zero if infeasibility not possible
                if sense == '>': 
                    zsign = 1 if error_term < 0 else -1  
                else:  #sense == '<':
                    zsign = -1 if error_term < 0 else 1

            zsign_list.append(zsign)

            # Compute Phi (scaled violation)
            percent_violation = violation / max(1, rhs)
            scaled_abs_violation = violation / constr_dict['coeff_inf-norm']
            phi_scale = alldata['algo_data']['phi_scale']
            if phi_scale == 'percent_violation':
                phi_z = percent_violation
            elif phi_scale == 'scaled_abs_violation':
                phi_z = scaled_abs_violation
            else:
                log.joint('ERROR: invalid phi_scale: %s\n'%(phi_scale))

            # Update the running max Phi of this z
            if phi_z > maxPhi_z:
                maxPhi_z = phi_z
                argmax_constr_z = constr_name
                argmax_zsign_z = zsign

            # Update sum of phis
            sumphis += phi_z

            # Track phi value
            argmax_phis_z[constr_name] = phi_z

            if loud: log.joint("    > constraint %s:  Phi = %g  for  %s = %g\n"%(constr_name, phi_z, coeff_dict['zvar'], zsign*budget))

        # Update the running max Phi
        if maxPhi_z > maxPhi:
            maxPhi = maxPhi_z
            argmax_constr = argmax_constr_z
            argmax_zsign = argmax_zsign_z
            argmax_zvar = coeff_dict['zvar']
            argmax_coeff = coeff
            argmax_phis = argmax_phis_z

        # Update running max sum phi
        if sumphis > maxsumphi:
            maxsumphi = sumphis
            argmaxsum_zsign_list = zsign_list
            argmaxsum_zvar = coeff_dict['zvar']
            argmaxsum_coeff = coeff

        if loud: log.joint("    Sum of phi_z's = %g\n"%sumphis)

    # Store max Phi and greedy data
    alldata['algo_data']['maxPhi'] = maxPhi
    alldata['algo_data']['argmax_constr'] = argmax_constr
    alldata['algo_data']['argmax_zsign'] = argmax_zsign
    alldata['algo_data']['argmax_zvar'] = argmax_zvar
    alldata['algo_data']['argmax_coeff'] = argmax_coeff
    alldata['algo_data']['argmax_phis'] = argmax_phis

    log.joint("\nGreedy Phi = %g\n"%(maxPhi))
    log.joint("  coeff: %g\n"%argmax_coeff)
    log.joint("  %s = %g\n"%(argmax_zvar, argmax_zsign*budget))
    log.joint("  max feature: %s\n"%argmax_constr)

    log.joint("\nGreedy max sum phis = %g\n"%(maxsumphi))
    log.joint("  coeff: %g\n"%argmaxsum_coeff)
    if len(set(argmaxsum_zsign_list)) != 1:
        log.joint("  INVALID: zvar changed sign across constraints!\n"%argmaxsum_coeff)
    else:
        log.joint("  %s = %g\n"%(argmaxsum_zvar, argmaxsum_zsign_list[0]*budget))

    return maxPhi


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