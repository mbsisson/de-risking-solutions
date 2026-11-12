###############################################################################
# Functions for solving model with chosen solver
#
# Blake Sisson mbs2246@columbia.edu
# 11/10/2026
###############################################################################
import time
import math
from drsk_ampl import drsk_store_vars, drsk_set_vars

def drsk_set_soln(alldata, soln_vector_dict):
    log = alldata['log']
    loud = alldata['loud']
    ampl = alldata['algo_data']['ampl']
    variables = alldata['prob_data']['variables']

    log.joint('Setting solution\n')

    X = ampl.get_variable("X")
    for varname in alldata['prob_data']['variables']:
        val = soln_vector_dict.get(varname, 0.0)
        idx = variables[varname]
        X[idx].set_value(val)

        x = ampl.get_variable(varname.lower())
        x.set_value(val)

        if loud: log.joint('  x%d %g\n'%(idx, val))

    Phi_L = ampl.get_variable('PHI_L')
    val = soln_vector_dict.get('Phi_L', 0.0)
    Phi_L.set_value(val)
    if loud: log.joint('  Phi_L %g\n'%(Phi_L.value()))


def drsk_check_soln(alldata):
    log = alldata['log']
    ampl = alldata['algo_data']['ampl']
    constraints = alldata['prob_data']['constraints']

    # Iterate through all constraints to find violations
    log.joint("Checking for violations...\n")
    count = 0
    for constr_name in constraints:
        # Check if the constraint is violated (negative slack means the bound is breached)
        constraint = ampl.get_constraint(constr_name)
        if constraint.slack() < -1e-6:
            count += 1
            log.joint(f"  Violation in {constr_name}:\n")
            log.joint(f"    Slack: {constraint.slack()}\n")
            log.joint(f"    Lower Bound: {constraint.lb()}, Upper Bound: {constraint.ub()}\n")
    log.joint(str(count) + " constraints violated\n\n")


def drsk_runSolver(alldata):
    ampl = alldata['algo_data']['ampl']
    ampl.solve()


def drsk_runSolver_knitro(alldata):
    log = alldata['log']
    ampl = alldata['algo_data']['ampl']

    # ampl settings for clean independent starts for each solve
    ampl.option["reset_initial_guesses"] = 0
    ampl.option["dual_initial_guesses"] = 0
    ampl.option["send_statuses"] = 0

    # store variable values before any solves
    vars_init = drsk_store_vars(alldata)

    log.joint('--- Standard Knitro run ---\n')
    ampl.set_option('knitro_options', 'outlev=1')
    ampl.solve()
    vars_stan = drsk_store_vars(alldata)
    obj_stan = ampl.get_objective('weighted_obj').value()
    log.joint(' Weighted obj: %f\n'%obj_stan)

    # reset variables
    drsk_set_vars(alldata, vars_init)

    log.joint('--- Concurrent Knitro run ---\n')
    ampl.set_option('knitro_options', 'concurrent_solver=1 outlev=1')
    ampl.solve()
    vars_conc = drsk_store_vars(alldata)
    obj_conc = ampl.get_objective('weighted_obj').value()
    log.joint(' Weighted obj: %f\n'%obj_conc)

    # reset variables
    drsk_set_vars(alldata, vars_init)

    log.joint('--- Multi-start Knitro run ---\n')
    ampl.set_option('knitro_options', 'ms_enable=1 outlev=1')
    ampl.solve()
    vars_ms = drsk_store_vars(alldata)
    obj_ms = ampl.get_objective('weighted_obj').value()
    log.joint(' Weighted obj: %f\n'%obj_ms)

    # vars_objs = [(obj_stan, vars_stan),
    #              (obj_conc, vars_conc),
    #              (obj_ms, vars_ms)]

    # # Get the entire tuple with the largest first entry
    # largest_tuple = max((vars_objs), key=lambda x: x[0])


def drsk_solve_model(alldata):
    retcode = 0

    log = alldata['log']
    ampl = alldata['algo_data']['ampl']
    solver = alldata['algo_data']['solver']
    solve_wrapper = alldata['algo_data']['solve_wrapper']
    variables = alldata['prob_data']['variables']
    constraints = alldata['prob_data']['constraints']
    soln_vector_dict = alldata['algo_data']['soln_vector_dict']
    timelimit = alldata['algo_data']['solve_time_limit']

    # Read in all parameters and sets
    ampl.get_parameter("Theta").set(alldata['prob_data']['Theta'])
    ampl.get_parameter("numcuts").set(alldata['cut_data']['numcuts'])
    ampl.get_set("nonzero_cutweights").set_values(alldata['cut_data']['nonzero_cutweights'])
    ampl.get_parameter("cutweights").set_values(alldata['cut_data']['cutweights'])
    ampl.get_set("nonzero_phiQuadWeights").set_values(alldata['cut_data']['nonzero_phiQuadWeights'])
    ampl.get_parameter("phiQuadWeights").set_values(alldata['cut_data']['phiQuadWeights'])
    ampl.get_set("nonzero_phiLinWeights").set_values(alldata['cut_data']['nonzero_phiLinWeights'])
    ampl.get_parameter("phiLinWeights").set_values(alldata['cut_data']['phiLinWeights'])
    ampl.get_parameter("phiConstWeights").set_values(alldata['cut_data']['phiConstWeights'])
    ampl.get_parameter("phiMinusToggle").set_values(alldata['cut_data']['phiMinusToggle'])

    # Solve
    log.joint("Solving model ...\n")
    log.joint("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")
    t0 = time.time()
    solve_wrapper(alldata)
    t1 = time.time()
    tdiff = t1 - t0
    log.joint("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n")                                                  
    log.joint("Solved with %s in %f seconds\n\n"%(solver, tdiff))

    # Check if solver time limit reached
    if tdiff > timelimit:
        retcode = 1

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

    # Store all variables
    # drsk_store_vars(alldata, alldata['algo_data']['all_vars'])

    # Store Phi_L
    alldata['algo_data']['Phi_L'] = ampl.get_variable('PHI_L').value()

    # Store cost
    alldata['algo_data']['cost'] = ampl.get_objective('obj').value()

    return retcode