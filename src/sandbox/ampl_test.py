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

def solve(alldata):
    log = alldata['log']
    ampl = alldata['ampl']
    solver = alldata['solver']
    variables = alldata['variables']
    soln_vector_dict = alldata['soln_vector_dict']

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
    for name, constraint in ampl.get_constraints():
        # Check if the constraint is violated (negative slack means the bound is breached)
        if constraint.slack() < -1e-6:
            count += 1
            log.joint(f"  Violation in {name}:\n")
            log.joint(f"    Slack: {constraint.slack()}\n")
            log.joint(f"    Lower Bound: {constraint.lb()}, Upper Bound: {constraint.ub()}\n")
    log.joint(str(count) + " constraints violated\n\n")

    
def eval_Phi_greedy(alldata, soln_vector_dict):
    log = alldata['log']
    loud = alldata['loud']
    all_constr_data = alldata['prob_data']['all_constr_data']
    structure = alldata['structure']
    budget = structure['budget']

    log.joint("Computing Phi using greedy method...\n")

    lhs_dict = {}  # Save lhs values for reused when applicable

    # Running max Phi(x) and correesponding constraint and z sign
    maxPhi = 0.0
    argmax_constr = ''
    argmax_zsign = 0
    argmax_zvar = ''

    # Loop over all z, i.e., unique risky coefficients
    for coeff, coeff_dict in structure['risky_coeffs'].items():
        # Running max Phi(|z) and correesponding constraint and z sign
        maxPhi_z = 0.0
        argmax_constr_z = ''
        argmax_zsign_z = 0

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

            # Compute Phi (scaled violation)
            percent_violation = violation / max(1, rhs)
            scaled_abs_violation = violation / constr_dict['coeff_inf-norm']
            phi_scale = alldata['algo']['phi_scale']
            if phi_scale == 'percent_violation':
                Phi_z = percent_violation
            elif phi_scale == 'scaled_abs_violation':
                Phi_z = scaled_abs_violation
            else:
                log.joint('ERROR: invalid phi_scale: %s\n'%(phi_scale))

            # Update the running max Phi of this z
            if Phi_z > maxPhi_z:
                maxPhi_z = Phi_z
                argmax_constr_z = constr_name
                argmax_zsign_z = zsign

            if loud: log.joint("    constraint %s:  Phi = %g  for  %s = %g\n"%(constr_name, Phi_z, coeff_dict['zvar'], zsign*budget))

        # Update the running max Phi
        if maxPhi_z > maxPhi:
            maxPhi = maxPhi_z
            argmax_constr = argmax_constr_z
            argmax_zsign = argmax_zsign_z
            argmax_zvar = coeff_dict['zvar']

    log.joint("Greedy Phi = %g\n"%(maxPhi))
    log.joint("  %s = %g\n"%(argmax_zvar, argmax_zsign*budget))
    log.joint("  max feature: %s\n"%argmax_constr)
    return maxPhi



if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('usage: ampl_test.py modfile')

    alldata = {}
    alldata['MODFILE'] = sys.argv[1]
    log = alldata['log'] = danoLogger('ampl_test.log')
    alldata['loud'] = True

    # Retrieve problem data and risk structure
    ampl = alldata["ampl"] = AMPL()
    readandstore(alldata)  #structure defined inside
    breakexit('Done parsing problem')

    # Solve and get solution x*
    solver = alldata["solver"] = "/Applications/knitro-16.0.0-ARM-MacOS/bin/knitroampl"
    soln_vector_dict = alldata["soln_vector_dict"] = {}
    solve(alldata)
    breakexit('Done solving problem')

    # Evaluate Phi(x*) and get z
    alldata['algo'] = {}
    alldata['algo']['phi_scale'] = 'percent_violation'  #'scaled_abs_violation'
    Phi = eval_Phi_greedy(alldata, soln_vector_dict)

    # Add cut
    # TODO

