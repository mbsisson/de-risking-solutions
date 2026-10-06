###############################################################################
# Functions for interacting with AmplPy:
#   1. parsing modfile and storing problem and structure data
#   2. solving model with chosen solver
#
# Blake Sisson mbs2246@columbia.edu
# 10/6/2026
###############################################################################
import re
import time
import math
import sympy as sp
from decimal import Decimal

RISKY_DECIMAL_THRESH = 3


def solve(alldata):
    log = alldata['log']
    ampl = alldata['algo_data']['ampl']
    solver = alldata['algo_data']['solver']
    variables = alldata['prob_data']['variables']
    constraints = alldata['prob_data']['constraints']
    soln_vector_dict = alldata['algo_data']['soln_vector_dict']

    # Read in all parameters and sets
    ampl.get_parameter("Theta").set(alldata['prob_data']['Theta'])
    ampl.get_parameter("numcuts").set(alldata['cut_data']['numcuts'])
    ampl.get_set("nonzero_cutweights").set_values(alldata['cut_data']['nonzero_cutweights'])
    ampl.get_parameter("cutweights").set_values(alldata['cut_data']['cutweights'])
    ampl.get_set("nonzero_phiQuadWeights").set_values(alldata['cut_data']['nonzero_phiQuadWeights'])
    ampl.get_parameter("phiQuadWeights").set_values(alldata['cut_data']['phiQuadWeights'])
    ampl.get_set("nonzero_phiLinWeights").set_values(alldata['cut_data']['nonzero_phiLinWeights'])
    ampl.get_parameter("phiLinWeights").set_values(alldata['cut_data']['phiLinWeights'])
    ampl.get_set("nonzero_phiConstWeights").set_values(alldata['cut_data']['nonzero_phiConstWeights'])
    ampl.get_parameter("phiConstWeights").set_values(alldata['cut_data']['phiConstWeights'])
    ampl.get_parameter("phiMinusToggle").set_values(alldata['cut_data']['phiMinusToggle'])
    

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
    for v in variables.keys():
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
    for constr_name in constraints:
        #Check if the constraint is violated (negative slack means the bound is breached)
        constraint = ampl.get_constraint(constr_name)
        if constraint.slack() < -1e-6:
            count += 1
            log.joint(f"  Violation in {name}:\n")
            log.joint(f"    Slack: {constraint.slack()}\n")
            log.joint(f"    Lower Bound: {constraint.lb()}, Upper Bound: {constraint.ub()}\n")
    log.joint(str(count) + " constraints violated\n\n")


def parse_ampl_constraint(alldata, expression, constr_name):
    """
    Parse an expanded AMPL constraint expression into linear/quadratic
    polynomial data. Also extract risky coefficient structure.
    (Based on code from ChatGPT 9/21/2026)

    Parameters
    ----------
    alldata : dic
        Dictionary of all data

    expression : str
        Expanded AMPL constraint, e.g.
            "x5^2 - 2*x8*x5 + x8^2 >= 9.143040659"

    variables : list
        List of all variables of problem.
        Effectively a 'word bank' and tracks variable indices

    name : str
        Constraint name, used only for error messages.

    Returns
    -------
    dict
        {
            "sense": "<=" or ">=" or "=",
            "RHS": float,
            "coeff_1-norm": float,
            "coeff_inf-norm": float,
            "constant": float,
            "lin_terms": {
                variable_name: (index, coefficient)
            },
            "quad_terms": {
                (variable1, variable2): (index, coefficient)
            }
        }
    """

    log = alldata['log']
    loud = alldata['loud']
    variables = alldata['prob_data']['variables']
    structure = alldata['struct_data']

    # ------------------------------------------------------------
    # 0. Clean up expression
    # ------------------------------------------------------------
    # Splitting by the character
    parts = expression.split(':')
    
    # Error check
    if len(parts) !=  2:
        raise ValueError(f"Constraint {constr_name}: {expression} is missing or contains multiple colons.")
        
    # Return the text after the character and drop the semicolon
    expression = parts[1].removesuffix(";")

    # ------------------------------------------------------------
    # 1. Extract sense and RHS
    # ------------------------------------------------------------
    match = re.search(r"(<=|>=|=)", expression)
    if match is None:
        raise ValueError(
            f"Could not find constraint sense in {constr_name} : {expression!r}"
        )

    # Get sense
    sense = match.group(1)

    # Get raw lhs
    lhs_string = expression[:match.start()].strip()

    # Process rhs
    rhs_string = expression[match.end():].strip().removesuffix(";")
    try:
        rhs = float(rhs_string)
    except ValueError as exc:
        raise ValueError(
            f"Could not parse RHS {rhs_string!r} "
            f"for constraint {constr_name!r}"
        ) from exc

    # ------------------------------------------------------------
    # 2. Convert AMPL syntax to SymPy syntax
    #    Warning: won't work if variable names contain '.' or brackets
    # ------------------------------------------------------------
    lhs_string = lhs_string.replace("^", "**")

    # Find AMPL variable names appearing in the expression.
    variable_pattern = re.compile(r"\b(?:" + "|".join(map(re.escape, variables.keys())) + r")\b")
    variable_names = list(dict.fromkeys(variable_pattern.findall(lhs_string)))
    symbols = {v: sp.Symbol(v) for v in variable_names}
    try:
        polynomial = sp.Poly(
            sp.expand(sp.sympify(lhs_string, locals=symbols)),
            *symbols.values()
        )
    except Exception as exc:
        raise ValueError(
            f"Could not parse polynomial for constraint {constr_name!r}:\n"
            f"{lhs_string}"
        ) from exc

    # ------------------------------------------------------------
    # 3. Separate constant / linear / quadratic terms
    # ------------------------------------------------------------
    constant = float(polynomial.TC())  # get constant term
    riskyconstr_flag = 0  # records if constraint has any risky coefficients (i.e., it is a feature)

    lin_terms = {}
    quad_terms = {}
    for powers, coeff in polynomial.terms():

        degree = sum(powers)
        coeff = float(coeff)

        # Check if coefficient is risky, i.e., has more than RISKY_DECIMAL_THRESH decimal points
        riskyterm_flag = 0  # records if term has risky coefficient
        if abs(Decimal(str(coeff)).as_tuple().exponent) >= RISKY_DECIMAL_THRESH:
            riskyconstr_flag = 1
            riskyterm_flag = 1

        # Constant term
        if degree == 0:
            continue

        # Linear term
        if degree == 1:
            var = variable_names[powers.index(1)]

            lin_terms[var] = coeff

        # Quadratic term
        elif degree == 2:
            vars_in_term = []

            for var, power in zip(variable_names, powers):
                vars_in_term.extend([var] * power)

            if len(vars_in_term) != 2:
                raise ValueError(
                    f"Unexpected quadratic term in constraint {constr_name!r}"
                )

            v1, v2 = sorted(vars_in_term)

            quad_terms[(v1, v2)] = coeff

        # Otherwise, problem
        else:
            raise ValueError(
                f"Constraint {constr_name!r} is not quadratic. "
                f"Found degree-{degree} term with powers {powers}."
            )
        
        # Store structure data if term has risky coefficient
        if riskyterm_flag:
            riskycoeff_dict = structure['risky_coeffs'].get(coeff)
            if riskycoeff_dict:
                # Coefficient already stored in risky_coeffs dictionary
                
                if riskycoeff_dict['instances'].get(constr_name):
                    # Coefficient already present in this constraint
                    if degree == 1:
                        riskycoeff_dict['instances'][constr_name].append(('linear', var))
                    else:  #degree == 2
                        riskycoeff_dict['instances'][constr_name].append(('quad', (v1, v2)))
                else:
                    # First instance of coefficient in this constraint
                    if degree == 1:
                        riskycoeff_dict['instances'][constr_name] = [('linear', var)]
                    else:  #degree == 2
                        riskycoeff_dict['instances'][constr_name] = [('quad', (v1, v2))]

            else:
                # First instance of this coefficient
                riskycoeff_dict = structure['risky_coeffs'][coeff] = {}
                riskycoeff_dict['index'] = index = structure['num_unique']
                riskycoeff_dict['zvar'] = 'z_' + str(index)
                riskycoeff_dict['instances'] = {}
                if degree == 1:
                    riskycoeff_dict['instances'][constr_name] = [('linear', var)]
                else:  #degree == 2
                    riskycoeff_dict['instances'][constr_name] = [('quad', (v1, v2))]
                structure['num_unique'] += 1

            if loud: 
                if degree == 1:
                    log.joint('    + coeff %g of var %s in constr %s is deemed risky\n'%(coeff, var, constr_name))
                else:  #degree == 2
                    log.joint('    + coeff %g of binomial %s in constr %s is deemed risky\n'%(coeff, (v1, v2), constr_name))
        
    # Update number of risky constraints
    structure['numfeats'] += riskyconstr_flag

    # ------------------------------------------------------------
    # 4. Coefficient norms
    #    Note: Norms of ALL nonconstant polynomial coefficients: 
    #       linear + quadratic coefficients.
    # ------------------------------------------------------------
    coefficients = [
        coefficient
        for coefficient in lin_terms.values()
    ] + [
        coefficient
        for coefficient in quad_terms.values()
    ]

    if coefficients:
        coeff_1_norm = sum(abs(c) for c in coefficients)
        coeff_inf_norm = max(abs(c) for c in coefficients)
    else:
        coeff_1_norm = 0.0
        coeff_inf_norm = 0.0

    # ------------------------------------------------------------
    # 5. Return data dictionary
    # ------------------------------------------------------------
    return {
        "sense": sense,
        "RHS": rhs,
        "degree": degree,
        "coeff_1-norm": coeff_1_norm,
        "coeff_inf-norm": coeff_inf_norm,
        "constant": constant,
        "lin_terms": lin_terms,
        "quad_terms": quad_terms,
    }


def read_and_store(alldata):
    log = alldata['log'] 
    loud = alldata['loud']
    ampl = alldata['algo_data']["ampl"]

    # Read modfile with AMPL
    ampl.read(alldata['MODFILE'])
    log.joint(f"Read file {alldata['MODFILE']} with AMPL\n")

    # Get list of all variables (remove artifical Phi_L and phi, and dummy X variables)
    variables = {}
    for var_data in ampl.get_variables():
        var_name = var_data[0]

        # Ignore artifical and dummy variables
        if var_name == 'PHI_L' or var_name == 'cutPHI_L' or var_name == 'phi' or var_name == 'X':
            continue

        # Retrieve variable index
        match = re.search(r'\d+$', var_name)
        var_idx = int(match.group())
        variables[var_name] = var_idx

    alldata['prob_data']['variables'] = variables
    log.joint("Num of variables = " + str(len(variables)) + " (excluding artifical and dummy vars)\n")

    #TODO assigned later, after first read
    #print("variables", variables)
    #print("features", alldata['prob_data']['features'])
    print('var_inds', list(variables.values()))
    ampl.get_set("var_inds").set_values(list(variables.values()))
    ampl.get_set("features").set_values(alldata['prob_data']['features'])
    ampl.get_parameter("Theta").set(0.0)
    ampl.get_parameter("numcuts").set(0)
    ampl.get_set("nonzero_cutweights").set_values(alldata['cut_data']['nonzero_cutweights'])
    ampl.get_parameter("cutweights").set_values(alldata['cut_data']['cutweights'])
    ampl.get_set("nonzero_phiQuadWeights").set_values(alldata['cut_data']['nonzero_phiQuadWeights'])
    ampl.get_parameter("phiQuadWeights").set_values(alldata['cut_data']['phiQuadWeights'])
    ampl.get_set("nonzero_phiLinWeights").set_values(alldata['cut_data']['nonzero_phiLinWeights'])
    ampl.get_parameter("phiLinWeights").set_values(alldata['cut_data']['phiLinWeights'])
    ampl.get_set("nonzero_phiConstWeights").set_values(alldata['cut_data']['nonzero_phiConstWeights'])
    ampl.get_parameter("phiConstWeights").set_values(alldata['cut_data']['phiConstWeights'])
    ampl.get_parameter("phiMinusToggle").set_values(alldata['cut_data']['phiMinusToggle'])

    # Retrieve problem data and structure of risky coefficients
    constraints = []
    all_constr_data = alldata["prob_data"]['all_constr_data']
    for constr_name, constr in ampl.get_constraints():
        # Skip artifical constraints
        if constr_name.startswith("defn_") or constr_name.startswith("Phicut"):
            if loud: log.joint(" - skipping %s\n"%constr_name)
            continue

        if loud: log.joint(' - attempting to read: %s\n'%constr_name)
        constraints.append(constr_name)
        all_constr_data[constr_name] = parse_ampl_constraint(alldata, constr.expand(), constr_name)

    # Store and display constraints
    #alldata['prob_data']['features'] = constraints
    log.joint("Num of constraints = " + str(len(list(ampl.get_constraints()))) + " (excluding artifical and dummy constraints)\n")
    log.joint("Retrieved problem data and structure\n")