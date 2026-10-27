###############################################################################
# Functions for computing the boosting step of the SOFTMAX-ADVERSARIAL 
# algorithm.
#
# Blake Sisson mbs2246@columbia.edu
# 10/27/2026
###############################################################################


def drsk_evalPhi_greedy(alldata, soln_vector_dict):
    log = alldata['log']
    loud = alldata['loud']
    verbose = alldata['verbose']
    all_constr_data = alldata['prob_data']['all_constr_data']
    structure = alldata['struct_data']
    budget = structure['budget']
    phi_scale = alldata['algo_data']['phi_scale']

    log.joint("Computing Phi using Greedy method...\n")

    # Save lhs values for reuse when applicable
    lhs_dict = {}

    # Save phi data for every coefficient
    all_phi_data = {}

    # Loop over all z, i.e., unique risky coefficients
    for coeff, coeff_dict in structure['risky_coeffs'].items():
        zvar = coeff_dict['zvar']

        # Running max Phi(|z) and corresponding constraint, z sign, 
        maxPhi_z = 0.0
        argmax_feat_z = 'None'
        argmax_zsign_z = 0

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
            if sense == '>=' or sense == '>':
                potential_violations = {0:0.0,
                                        -1:rhs - (lhs - error_term),
                                        1:rhs - (lhs + error_term)}
                zsign, violation = max(potential_violations.items(), key=lambda x: x[1])
                if verbose: log.joint("DEBUG: Determine max violation of %s constraint\n"%sense)
                if verbose: log.joint("DEBUG:  0, %g, or %g\n"%(potential_violations[-1], potential_violations[1]))
            elif sense == '<=' or sense == '<':
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

            # Compute Phi (scaled violation)
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

            if loud: log.joint("    > constraint %s:  Phi = %g  for  %s = %g\n"%(constr_name, phi_z, zvar, zsign*budget))

        # Save all phi data for this zvar
        all_phi_data[zvar] = {}
        all_phi_data[zvar]['maxPhi'] = maxPhi_z
        all_phi_data[zvar]['argmax_feat'] = argmax_feat_z
        all_phi_data[zvar]['argmax_zsign'] = argmax_zsign_z
        all_phi_data[zvar]['coeff'] = coeff  # stored elsewhere, but nice to have here

    # Sort zvars by phi max value in descending order
    sorted_zvars = sorted(all_phi_data, key=lambda z: all_phi_data[z]['maxPhi'], reverse=True)
    all_phi_data['sorted_zvars'] = sorted_zvars

    log.joint("Top 10 Phi's\n")
    for i in range(min(10, len(sorted_zvars))):
        zvar = sorted_zvars[i]
        phi_data = all_phi_data[zvar]
        maxPhi_z = phi_data['maxPhi']
        coeff = phi_data['coeff']
        argmax_zsign_z = phi_data['argmax_zsign']
        argmax_feat_z = phi_data['argmax_feat']
        log.joint(" %2d. phi=%g  feat=%s  coeff=%g  %s=%g\n"%(i+1, maxPhi_z, argmax_feat_z, coeff, zvar, argmax_zsign_z*budget))

    alldata['algo_data']['all_phi_data'] = all_phi_data

    # Return max Phi
    log.joint("Done computing Phi using Greedy.\n\n")
    return all_phi_data[sorted_zvars[0]]['maxPhi']