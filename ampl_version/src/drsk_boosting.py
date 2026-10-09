###############################################################################
# Functions for computing the boosting step of the SOFTMAX-ADVERSARIAL 
# algorithm.
#
# Blake Sisson mbs2246@columbia.edu
# 10/7/2026
###############################################################################

def evalPhi_greedy(alldata, soln_vector_dict):
    log = alldata['log']
    loud = alldata['loud']
    verbose = alldata['verbose']
    all_constr_data = alldata['prob_data']['all_constr_data']
    structure = alldata['struct_data']
    budget = structure['budget']

    log.joint("Computing Phi using greedy method...\n")

    lhs_dict = {}  # Save lhs values for reused when applicable

    # Running max Phi(x) with corresponding: constraint, z sign, z variable, and coefficient
    maxPhi = 0.0
    argmax_feat = ''
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
        argmax_feat_z = ''
        argmax_zsign_z = 0
        argmax_phis_z = {}  # phi values for each feature greedily using this zvar, Dict: feat_name --> phi_i(x^t | z^t = greedy(zvar, budget))

        # Running sum of phi's, i.e., sum of violations
        sumphis = 0.0

        # Record list of z signs to track changes
        zsign_list = []

        if loud: log.joint("  Coeff %g\n"%(coeff))

        # Loop over all constraints this risky coefficient appears in
        for constr_name, constr_instance_list in coeff_dict['instances'].items():
            constr_dict = all_constr_data[constr_name]
            rhs = constr_dict['RHS']
            if verbose: log.joint("DEBUG: rhs = %g\n"%(rhs))

            # Compute LHS
            lhs = lhs_dict.get(constr_name)
            if not lhs:
                if verbose: log.joint("DEBUG: Computing LHS of %s\n"%constr_name)
                # Constant
                lhs = constr_dict['constant']
                if verbose: log.joint("DEBUG:  + const = %g\n"%constr_dict['constant'])
                # Linear terms
                for v, c in constr_dict['lin_terms'].items():
                    v_val = soln_vector_dict[v]
                    lhs += c * v_val
                    if verbose: log.joint("DEBUG:  + coeff * %s = %g * %g\n"%(v, c, v_val))
                # Quadratic terms
                for v_tuple, c in constr_dict['quad_terms'].items():
                    v1, v2 = v_tuple[0], v_tuple[1]
                    v1_val, v2_val = soln_vector_dict[v1], soln_vector_dict[v2]
                    lhs += c * v1_val * v2_val
                    if verbose: log.joint("DEBUG:  + coeff * %s * %s = %g * %g\n"%(v1, v2, c, v_val))
                lhs_dict[constr_name] = lhs
            if verbose: log.joint("DEBUG: lhs = %g\n"%(lhs))

            # Compute error term (from setting z = budget, for z corresponding to coeff)
            error_term = 0.0
            if verbose: log.joint("DEBUG: Computing error term of constraint %s and coeff %g\n"%(constr_name, coeff))
            for degree, var in constr_instance_list:
                if degree == 'quad':
                    v1, v2 = var[0], var[1]
                    v1_val, v2_val = soln_vector_dict[v1], soln_vector_dict[v2]
                    error_term += v1_val * v2_val
                    if verbose: log.joint("DEBUG:  + coeff * budget * %s * %s = %g * %g * %g * %g\n"%(v1, v2, coeff, budget, v1_val, v2_val))
                else:  #linear
                    var_val = soln_vector_dict[var]
                    error_term += var_val
                    if verbose: log.joint("DEBUG:  + coeff * budget * %s = %g * %g * %g\n"%(var, coeff, budget, var_val))
            error_term *= coeff * budget  #save repetitive multiplcation for last
            if verbose: log.joint("DEBUG: error term = %g\n"%(error_term))

            # Get constraint sense
            sense = constr_dict['sense']

            # Determine max violation and corresponding zvar value (-1, 1, or 0 if no violation possible)
            if sense == '>=':
                potential_violations = {0:0.0,
                                        -1:rhs - (lhs - error_term),
                                        1:rhs - (lhs + error_term)}
                zsign, violation = max(potential_violations.items(), key=lambda x: x[1])
                if verbose: log.joint("DEBUG: Determine max violation of %s constraint\n"%sense)
                if verbose: log.joint("DEBUG:  0, %g, or %g\n"%(potential_violations[-1], potential_violations[1]))
            elif sense == '<=':
                potential_violations = {0:0.0,
                                        -1:lhs - error_term - rhs,
                                        1:lhs + error_term - rhs}
                zsign, violation = max(potential_violations.items(), key=lambda x: x[1])
                if verbose: log.joint("DEBUG: Determine max violation of %s constraint\n"%sense)
                if verbose: log.joint("DEBUG:  0, %g, or %g\n"%(potential_violations[-1], potential_violations[1]))
            else:  # sense == '='
                potential_violations = {0:0.0,
                                        -1:abs(lhs - error_term - rhs),
                                        1:abs(lhs + error_term - rhs)}
                zsign, violation = max(potential_violations.items(), key=lambda x: x[1])
                if verbose: log.joint("DEBUG: Determine max violation of %s constraint\n"%sense)
                if verbose: log.joint("DEBUG:  0, %g, or %g\n"%(potential_violations[-1], potential_violations[1]))
            if verbose: log.joint("DEBUG: violation of %g possible by setting z sign = %d\n"%(violation, zsign))

            zsign_list.append(zsign)

            # Compute Phi (scaled violation)
            phi_scale = alldata['algo_data']['phi_scale']
            if phi_scale == 'percent_violation':
                phi_z = violation / max(1, rhs)
            elif phi_scale == 'scaled_abs_violation':
                phi_z = violation / constr_dict['coeff_inf-norm']
            else:
                log.joint('ERROR: invalid phi_scale: %s\n'%(phi_scale))
            if verbose: log.joint("DEBUG: phi (scaled violation) = %g\n"%(phi_z))

            # Update the running max Phi of this z
            if phi_z > maxPhi_z:
                maxPhi_z = phi_z
                argmax_feat_z = constr_name
                argmax_zsign_z = zsign

            # Update sum of phis
            sumphis += phi_z

            # Track phi value
            argmax_phis_z[constr_name] = phi_z

            if loud: log.joint("    > constraint %s:  Phi = %g  for  %s = %g\n"%(constr_name, phi_z, coeff_dict['zvar'], zsign*budget))

        # Update the running max Phi
        if maxPhi_z > maxPhi:
            maxPhi = maxPhi_z
            argmax_feat = argmax_feat_z
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
    alldata['algo_data']['argmax_feat'] = argmax_feat
    alldata['algo_data']['argmax_zsign'] = argmax_zsign
    alldata['algo_data']['argmax_zvar'] = argmax_zvar
    alldata['algo_data']['argmax_coeff'] = argmax_coeff
    alldata['algo_data']['argmax_phis'] = argmax_phis

    log.joint("Greedy Phi = %g\n"%(maxPhi))
    log.joint("  coeff: %g\n"%argmax_coeff)
    log.joint("  %s = %g\n"%(argmax_zvar, argmax_zsign*budget))
    log.joint("  max feature: %s\n"%argmax_feat)

    log.joint("Greedy max sum phis = %g\n"%(maxsumphi))
    log.joint("  coeff: %g\n"%argmaxsum_coeff)
    if len(set(argmaxsum_zsign_list)) != 1:
        log.joint("  INVALID: zvar changed sign across constraints!\n")
    else:
        log.joint("  %s = %g\n"%(argmaxsum_zvar, argmaxsum_zsign_list[0]*budget))

    log.joint("Computed Phi using Greedy\n\n")
    return maxPhi