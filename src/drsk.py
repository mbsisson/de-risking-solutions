import gurobipy as gp
import numpy as np
import torch
from drskred import drsk_softmax


# =============================================================================
# EVALUATE phi_max
# =============================================================================

def drsk_getimpact_greedy(alldata, solutionvectordict, loud=False):
    '''
    Computes the max impact (phi_max) using the greedy method.
    For each feature, determine the risky term (i.e. monomial subject to coefficient error)
    with the greatest magnitude of constraint violation (when corresponding zvar = budget):
        |xsoln*coeff*budget| for equalities, or
        (|xsoln*coeff*budget| - slack) for inequalities,
    Place all budget on risky term with greatest magnitude across 
    all features.

    Can handle linear and quadratic features.
    Stores data in alldata['algo'].
    '''
    log = alldata['log']
    budget = alldata['algo']['budget']
    structure = alldata['structure']
    set = structure['set']
    I = structure['I']
    linconstrs = alldata['LP']['linconstrs']  #local objects, not Gurobi linear constraint
    quadconstrs = alldata['LP']['quadconstrs']  #local objects, not Gurobi quadratic constraint

    impacts = alldata['algo']['impacts']
    indmax = alldata['algo']['indmax']
    zvalues = alldata['algo']['zvalues']

    log.joint('Getting max impact at iteration %d using greedy\n' %(alldata['algo']['iteration_cnt']))

    # Auxiliary memory for logging
    maxriskyterms = alldata['algo']['maxriskyterms']
    senses = alldata['algo']['senses']
    slacks = alldata['algo']['slacks']
    RHSs = alldata['algo']['RHSs']
    max_scaled_abs_violations = alldata['algo']['max_scaled_abs_violations']
    max_percent_violations = alldata['algo']['max_percent_violations']

    maxfeature = 0  #value of feature with greatest magnitude risky term
    maxfeaturename = ''  #name of maxfeature
    indmaxfeature = -1  #index of greatest magnitude risky term in maxfeature

    for i in range(I):  #for each feature
        seti = set[i]
        namei = seti['featurename']  #feature name
        numriskyi = seti['numrisky']  #number of risky coefficients in feature
        if loud: log.joint('>feat: {}  name: {}  numrisky: {}\n'.format(i, namei, numriskyi))

        maxterm = 0  #value of risky term with greatest magnitude in this feature
        maxtermname = ''  #name of zvar corresponding to maxterm
        indmaxterm = -1  #index of maxterm
        zsignmaxterm = 0  #sign of corresponding zvar needed to cause violation

        # Get feature data (different for quadratic and linear constraints)

        if seti['isQuadratic']:  #Feature is quadratic
            qc = quadconstrs[namei]  #quadratic constraint feature corresponds to
            sense = qc['sense']
            fieldLin = qc['lin']  #dict: variable name --> (index, coefficient of term w/ variable)
            fieldQuad = qc['quad']  #dict: variable tuple --> (index, coefficient of term w/ variable)
            rhs = qc['RHS']
            coeff_1norm = qc['coeff_1-norm']
            inf_norm = qc['inf_norm']

            # Compute lhs of current solution
            lhs = 0
            for varname, coeff_data in fieldLin.items():
                coeff = coeff_data[1]
                xval = solutionvectordict[varname]
                lhs += coeff * xval
            for vartuple, coeff_data in fieldQuad.items():
                coeff = coeff_data[1]
                varname1, varname2 = vartuple[0], vartuple[1]
                xyval = solutionvectordict[varname1] * solutionvectordict[varname2]
                lhs += coeff * xyval

        else:  #Feature is linear
            lc = linconstrs[namei]  #linear constraint feature corresponds to
            sense = lc['sense']
            fieldLin = lc['field']  #dict: variable name --> (index, coefficient of term w/ variable)
            rhs = lc['RHS']
            coeff_1norm = lc['coeff_1-norm']
            inf_norm = lc['inf_norm']

            # Compute lhs of current solution
            lhs = 0
            for varname, coeff_data in fieldLin.items():
                coeff = coeff_data[1]
                xval = solutionvectordict[varname]
                lhs += coeff*xval

        # Compute slack of feature
        if sense == '>':
            slacki = lhs - rhs
        elif sense == '<':
            slacki = rhs - lhs
        else:
            slacki = 0

        for j in range(numriskyi): #for each risky coefficient
            listij = seti['list'][j]
            zvar = listij[0]  #z variable corresponsing to coefficient
            card = listij[1]  #number of terms using by coefficient (1 for us)
            arrvars = listij[2]  #x variable(s) corresponding to coefficient
            if loud: log.joint(' >riskyterm: {}  z: {}  card: {}  vars: {}\n'.format(j, zvar, card, arrvars))   

            valriskytermj = 0  #value of risky term at current solution
            for h in range(card): #structure, for us card == 1 always (bc assuming risky coefficients are 'independent')
                expression = arrvars[h]  #x varible(s) corresponding to risky coefficient
                if isinstance(expression, tuple):
                    # Quadratic term
                    xyval = solutionvectordict[expression[0]] * solutionvectordict[expression[1]]  #value of monomial at current solution
                    coeff = fieldQuad[expression][1]
                    if loud: log.joint('  j={} h={} var={} xyval={} coeff={}\n' .format(j, h, arrvars[h], xyval, coeff))
                    valriskytermj += xyval*coeff*budget
                else:
                    # Linear term
                    xval = solutionvectordict[expression]  #value of x varible at current solution
                    coeff = fieldLin[expression][1]
                    if loud: log.joint('  j={} h={} var={} xval={} coeff={}\n' .format(j, h, arrvars[h], xval, coeff))
                    valriskytermj += xval*coeff*budget

            # Compute violation (i.e. raw impact). Depends on feature sense (=, >, <)
        
            if sense == '=':  #Feature is equality constraint
                violation = valriskytermj
                zsign = 1 if violation < 0 else -1

            else: #Feature is inequality constraint
                if np.abs(valriskytermj) > slacki:  #risky coefficient CAN cause infeasibility
                    violation = np.abs(valriskytermj) - slacki
                else:  #risky coefficient CANNOT cause infeasibility
                    violation = 0

                # Sign of z to adjust coefficient towards infeasibility
                if sense == '>':  #Feature is geq constraint
                    zsign = 1 if valriskytermj < 0 else -1  
                else:  #sense == '<':  Feature is leq constraint
                    zsign = -1 if valriskytermj < 0 else 1

            # Compute impact based on appropriate scalant

            percent_violation = violation / max(1, rhs)
            scaled_abs_violation = violation / inf_norm

            if alldata['algo']['phi_scale'] == 'percent_violation':
                impact = percent_violation
            elif alldata['algo']['phi_scale'] == 'scaled_abs_violation':
                impact = scaled_abs_violation
            else:
                log.joint('ERROR: invalid phi_scale: %s\n'%(alldata['algo']['phi_scale']))
                return None

            if loud: log.joint('  z_ij=%.3g -> violation %.3e , impact %.3e\n' %(zsign*budget, violation, impact))
            
            # Update running max risky term if this term has greater impact
            if np.abs(impact) > maxterm:
                maxterm = np.abs(impact)
                maxtermname = zvar
                indmaxterm = j
                zsignmaxterm = zsign

                # Extra info for logging
                max_scaled_abs_violations[i] = scaled_abs_violation
                max_percent_violations[i] = percent_violation
                maxriskyterms[i] = str(arrvars)  #store variables associated with this risky term

        # Store impact of this feature
        impacts[i] = maxterm  #largest impact over all risky terms in this feature
        indmax[i] = indmaxterm  #index of risky term with greatest impact
        zvalues[i] = budget*zsignmaxterm  #value of corresponding z variable

        # Extra info for logging
        senses[i] = sense
        slacks[i] = slacki
        RHSs[i] = rhs

        # Update running max feature if this feature has greater impact
        if maxterm > maxfeature:
            maxfeature = maxterm
            maxfeaturename = maxtermname
            indmaxfeature = i

        if loud:
            log.joint(' SUMMARY - feat: %s (%s)  Greedy: %g at term: %s (idx %d)\n' %(namei, sense, maxterm, maxtermname, indmaxterm))
            log.joint('           feature details: slack: %g  inf-norm: %g  rhs: %g\n'%(slacki, inf_norm, rhs))

    log.joint('Max feature value: %g at %s\n' %(maxfeature, maxfeaturename))
    alldata['algo']['indmaxfeature'] = indmaxfeature
    foo = np.argsort(-impacts)
    for h in range(I):
        i = foo[h]
        if impacts[i] <= 0:
            break

        if loud:
            featname = structure['set'][i]['featurename']
            log.joint('Counter: %d  feature: %s (%s)  term: %s  z=%.3g --> impact: %.3e\n' %(h, featname, senses[i], maxriskyterms[i], zvalues[i], impacts[i]))
            log.joint('         rhs: %.3f  slack: %.3f  percent_violation: %.3f  scaled_abs_violation: %.3f\n'%(RHSs[i], slacks[i], max_percent_violations[i], max_scaled_abs_violations[i]))

    return impacts[foo[0]]

def drsk_getimpact_softmax(alldata, solutionvectordict):
    log = alldata['log']
    structure = alldata['structure']
    budget = alldata['algo']['budget']
    set = structure['set']
    I = structure['I']
    linconstrs = alldata['LP']['linconstrs']
    quadconstrs = alldata['LP']['quadconstrs']

    log.joint('Getting impact at iteration_cnt %d using SOFTMAX.\n' %(alldata['algo']['iteration_cnt']))

    # Store data pertinent to computing impact via SOFTMAX-ADVERSARIAL (log-sum-exp)
    alldata['softmax'] = {}
    alldata['softmax']['budget'] = budget
    alldata['softmax']['I'] = I
    alldata['softmax']['alpha'] = alldata['algo']['alpha']

    # compute dimension of z, i.e. total num of risky coefficients. TODO: should do ahead of time
    zdim = 0
    for i in range(I):
        zdim += set[i]['numrisky']

    featuredata = alldata['softmax']['features'] = []  #TODO: should be stored ahead of time, not each iteration?
    zidx = 0  # first z variable of current feature
    for i in range(I): # for each feature
        if set[i]['numrisky'] == 0:
            #skip riskless constraints
            continue

        feati = {}
        featuredata.append(feati)
        feati['i'] = i

        seti = set[i]
        name = seti['featurename']  # feature name
        feati['name'] = name
        numriskyi = seti['numrisky']  # number of risky coefficients in feature
        feati['numrisky'] = numriskyi
        log.joint('>feat: {}  name: {}  numrisky: {}\n'.format(i, name, numriskyi))

        if seti['isQuadratic']:  # Feature is quadratic
            qc = quadconstrs[name]
            sense = qc['sense']
            fieldLin = qc['lin']
            fieldQuad = qc['quad']
            rhs = qc['RHS']
            coeff_1norm = qc['coeff_1-norm']
            inf_norm = qc['inf_norm']

            # Compute LHS of current solution
            lhs = 0
            for varname, coeff_data in fieldLin.items():
                coeff = coeff_data[1]
                xval = solutionvectordict[varname]
                lhs += coeff * xval
            for vartuple, coeff_data in fieldQuad.items():
                coeff = coeff_data[1]
                varname1, varname2 = vartuple[0], vartuple[1]
                xyval = solutionvectordict[varname1] * solutionvectordict[varname2]
                lhs += coeff * xyval

        else:  # Feature is linear
            lc = linconstrs[name]  # linear constraint feature corresponds to
            sense = lc['sense']
            fieldLin = lc['field']  # dict: variable name --> (index, coefficient of term w/ variable)
            rhs = lc['RHS']
            coeff_1norm = lc['coeff_1-norm']  #for scaling displacement (i.e. impact)
            inf_norm = lc['inf_norm']

            # Compute LHS of current solution
            lhs = 0
            for varname, coeff_data in fieldLin.items():
                coeff = coeff_data[1]
                xval = solutionvectordict[varname]
                #lhs_vec.append(coeff*xval)
                lhs += coeff*xval

        feati['sense'] = sense
        # Set phi scale
        if alldata['algo']['phi_scale'] == 'percent_violation':
            feati['scale'] = max(rhs, 1)
        elif alldata['algo']['phi_scale'] == 'scaled_abs_violation':
            feati['scale'] = inf_norm
        else:
            log.joint('ERROR: invalid phi_scale: %s\n'%(alldata['algo']['phi_scale']))

        # Compute risky expression: vector_{j: risky} a_ij f_ij(x) z_ij
        riskyexpr = []  #riskyexpr vector
        for j in range(numriskyi): # for each risky coefficient
            listij = seti['list'][j]
            zvar = listij[0]  # z variable corresponsing to coefficient
            card = listij[1]  # number of x varibles in term, just 1 for linear constraints
            arrvars = listij[2]  # x variable corresponding to coefficient
            log.joint(' >riskyterm: {}  z: {}  card: {}  vars: {}\n'.format(j, zvar, card, arrvars))   

            #valriskytermj = 0  # value of risky term at current solution
            for h in range(card):
                expression = arrvars[h]  # x varible corresponding to risky coefficient
                if isinstance(expression, tuple):  # quadratic term
                    xyval = solutionvectordict[expression[0]] * solutionvectordict[expression[1]]
                    coeff = fieldQuad[expression][1]
                    log.joint('  j={} h={} var={} xyval={} coeff={}\n' .format(j, h, arrvars[h], xyval, coeff))
                    riskyexpr.append(coeff * xyval)
                else:  # linear term
                    xval = solutionvectordict[expression]  # value of x varible at current solution
                    coeff = fieldLin[expression][1]  # coefficient value
                    log.joint('  j={} h={} var={} xval={} coeff={}\n' .format(j, h, arrvars[h], xval, coeff))
                    riskyexpr.append(coeff * xval)

        # Embedd risky expression vector into length zdim
        embedded_riskyexpr = np.zeros(zdim)
        embedded_riskyexpr[zidx: zidx+numriskyi] = riskyexpr
        zidx = zidx+numriskyi
        feati['riskyexpr'] = torch.tensor(embedded_riskyexpr, dtype=torch.float32)

        # define slack
        if sense == '>':
            feati['slack'] = lhs - rhs
        elif sense == '<':
            feati['slack'] = rhs = lhs
        else:
            feati['slack'] = 0

    # Memory for Red solution
    zvalues = alldata['algo']['zvalues'] = np.zeros(zdim)

    alldata['softmax']['zdim'] = zdim
    drsk_softmax(alldata, loud=True)

    # Memory for max impact given Red solution, i.e. \phi^t_\max
    #deltas = alldata['algo']['deltas']
    #indmax = alldata['algo']['indmax']
    

    ############# TODO: Below could be its own function ################
    maxfeature = 0
    maxfeaturename = ''
    indmaxfeature = -1

    # Memory for storing feature values of current Blue and Red solutions, i.e. phi_i(x^t|z^t)
    phi_ixz = alldata['softmax']['phi_ixz'] = np.zeros(I)

    zidx = 0
    for i in range(I): # for each feature
        seti = set[i]
        if seti['numrisky'] == 0: continue  #TODO: redundant? I probably is already only features containing risky coefficients
        name = seti['featurename']  # feature name
        numriskyi = seti['numrisky']  # number of risky coefficients in feature

        feati = featuredata[i]
        if feati['i'] != i:
            log.joint('PROBLEM: featuredata out of sync.\n')
        sense = feati['sense']
        scale = feati['scale']
        slack = feati['slack']

        if seti['isQuadratic']:  # Feature is quadratic
            qc = quadconstrs[name]
            sense = qc['sense']
            fieldLin = qc['lin']
            fieldQuad = qc['quad']
            rhs = qc['RHS']
        else:  # Feature is linear
            lc = linconstrs[name]  # linear constraint feature corresponds to
            sense = lc['sense']
            fieldLin = lc['field']  # dict: variable name --> (index, coefficient of term w/ variable)
            rhs = lc['RHS']

        valriskyexpr = 0
        for j in range(numriskyi): # for each risky coefficient
            listij = seti['list'][j]
            zvar = listij[0]  # z variable corresponsing to coefficient
            card = listij[1]  # number of x varibles in term
            arrvars = listij[2]  # x variable corresponding to coefficient

            valriskytermj = 0  # value of risky term at current solution
            for h in range(card): # structure
                expression = arrvars[h]  # x varible corresponding to risky coefficient
                if isinstance(expression, tuple):
                    # quadratic term
                    xyval = solutionvectordict[expression[0]] * solutionvectordict[expression[1]]
                    coeff = fieldQuad[expression][1]
                    valriskytermj += xyval*coeff*zvalues[zidx]
                else:
                    # linear term
                    xval = solutionvectordict[expression]  # value of x varible at current solution
                    coeff = fieldLin[expression][1]  # coefficient value
                    valriskytermj += xval*coeff*zvalues[zidx]

            valriskyexpr += valriskytermj
            zidx += 1

        # displacement and signscore depends on feature sense (=, >, <)
        if sense == '=':  # Feature is equality constraint
            displacement = abs(valriskyexpr) / scale
        elif sense == '>':  # Feature is geq constraint
            displacement = max(0, -valriskyexpr - slack) / scale
        else:  # sense == '<':  Feature is leq constraint
            displacement = max(0, valriskyexpr - slack) / scale

        phi_ixz[i] = displacement

        if np.abs(displacement) > maxfeature:  #consistent with greedy
            maxfeature = displacement
            maxfeaturename = name
            indmaxfeature = j

    log.joint('Max impact: %f  feature: %s (idx=%d)\n' %(maxfeature, maxfeaturename, indmaxfeature))
    return maxfeature


# =============================================================================
# ADD CUTS
# =============================================================================

def drsk_add_impactvar(alldata):
    log = alldata['log']
    retcode = 0
    condition = 'add_impactvar'
    givenTheta = False

    if alldata['algo'].get('theta') is None:
        # Use objective and impact from first iteration
        cost_initial = alldata['algo']['iterations'][0]['cost'] 
        phi_max_initial = alldata['algo']['iterations'][0]['phi_max']

        lambda_lo = alldata['algo']['lambda_lo']
        lambda_hi = alldata['algo']['lambda_hi']
        xi = alldata['algo']['xi']

        theta = (cost_initial * xi) / (phi_max_initial * (lambda_hi - lambda_lo))

        alldata['algo']['theta'] = theta 
        alldata['algo']['targetimpact'] = lambda_hi * phi_max_initial
        alldata['algo']['targetcost'] = (1 + (lambda_hi * xi)/(lambda_hi - lambda_lo)) * cost_initial

    else:
        # Theta value given, so use that instead
        theta = alldata['algo']['theta']
        givenTheta = True

    log.joint('Adding impact variable with Theta %g.\n' %(theta))
    gurobimodel = alldata['gurobimodel']
    alldata['LP']['Phi_L'] = gurobimodel.addVar(name = "Phi_L", obj = theta)
    alldata['algo']['givenTheta'] = givenTheta
   
    return retcode, (condition)

def drsk_add_greedycuts(alldata, loud=False):
    '''Adds greedy cut corresponding to largest risky term over all features'''
    retcode = 0
    condition = ('add_greedycuts')
    log = alldata['log']
    iteration = alldata['algo']['iteration_cnt']
    structure = alldata['structure']
    set = structure['set']
    gurobimodel = alldata['gurobimodel']
    linconstrs = alldata['LP']['linconstrs']
    quadconstrs = alldata['LP']['quadconstrs']
    
    Phi_L = alldata['LP']['Phi_L'] 
    indmax = alldata['algo']['indmax']
    zvalues = alldata['algo']['zvalues']

    log.joint('Adding greedy cuts at iteration_cnt %d.\n' %(iteration))

    indmaxfeature = alldata['algo']['indmaxfeature'] # max feature (constraint) impact
    seti = set[indmaxfeature]
    namei = seti['featurename']  # name of max feature
    indi = indmax[indmaxfeature]  # index of this feature's risky term of greatest magnitude
    zvali = zvalues[indmaxfeature]  # budget or -budget (depending on sign of this feature's risky term of greatest magnitude)

    listij = seti['list'][indi]
    zvar = listij[0]
    card = listij[1]
    arrvars = listij[2]

    # Construct expression for cut

    if seti['isQuadratic']:  # Greedy risky feature is quadratic
        qc = quadconstrs[namei]
        fieldLin = qc['lin']
        fieldQuad = qc['quad']
        sense = qc['sense']
        rhs = qc['RHS']
        coeff1norm = qc['coeff_1-norm']
        inf_norm = qc['inf_norm']

        # Compute risky expression, terms with computed Red z
        riskyexpr = gp.QuadExpr()
        for h in range(card):
            expression = arrvars[h]
            if isinstance(expression, tuple):  # quadratic term
                coeff = fieldQuad[expression][1]
                gurobivar1 = gurobimodel.getVarByName(expression[0])
                gurobivar2 = gurobimodel.getVarByName(expression[1])
                if loud:
                    log.joint('Greedy cut on feature: %s (%s) <-- quadratic constraint, quadratic term\n'%(namei, sense))
                    log.joint("risky expression: %s = (%f,%f)  coeff: %f  zval: %f\n"%(expression, gurobivar1.X, gurobivar2.X, coeff, zvali))
                riskyexpr += coeff*zvali*gurobivar1*gurobivar2  # infeasibility (change to largest term)
            else:  # linear term
                coeff = fieldLin[expression][1]
                gurobivar = gurobimodel.getVarByName(expression)
                if loud:
                    log.joint('Greedy cut on feature: %s (%s) <-- quadratic constraint, linear term\n'%(namei, sense))
                    log.joint("risky expression: %s = %f  coeff: %f  zval: %f\n"%(expression, gurobivar.X, coeff, zvali))
                riskyexpr += coeff*zvali*gurobivar  # infeasibility (change to largest term)

        # Compute nominal expression, lhs(x), needed for slack
        nominalexpr = gp.QuadExpr()
        for varname, coeff_data in fieldLin.items():
            coeff = coeff_data[1]
            gurobivar = gurobimodel.getVarByName(varname)
            nominalexpr += coeff*gurobivar
        for vartuple, coeff_data in fieldQuad.items():
            coeff = coeff_data[1]
            varname1, varname2 = vartuple[0], vartuple[1]
            gurobivar1 = gurobimodel.getVarByName(varname1)
            gurobivar2 = gurobimodel.getVarByName(varname2)
            nominalexpr += coeff*gurobivar1*gurobivar2

    else:  # Greedy risky feature is linear
        lc = linconstrs[namei]
        fieldLin = lc['field']
        sense = lc['sense']
        rhs = lc['RHS']
        coeff1norm = lc['coeff_1-norm']
        inf_norm = lc['inf_norm']

        # Compute risky expression, terms with computed Red z
        riskyexpr = gp.LinExpr()
        for h in range(card):
            expression = arrvars[h]
            coeff = fieldLin[expression][1]
            gurobivar = gurobimodel.getVarByName(expression)
            if loud:
                log.joint('Greedy cut on feature: %s (%s) <-- linear constraint\n'%(namei, sense))
                log.joint("risky expression: %s = %f  coeff: %f  zval: %f\n"%(expression, gurobivar.X, coeff, zvali))
            riskyexpr += coeff*zvali*gurobivar  # infeasibility (change to largest term)
    
        # Compute nominal expression, lhs(x), needed for slack
        nominalexpr = gp.LinExpr()
        for varname, coeff_data in fieldLin.items():
            coeff = coeff_data[1]
            gurobivar = gurobimodel.getVarByName(varname)
            nominalexpr += coeff*gurobivar

    # Set phi scale
    if alldata['algo']['phi_scale'] == 'percent_violation':
        phi_scale = max(rhs, 1)
    elif alldata['algo']['phi_scale'] == 'scaled_abs_violation':
        phi_scale = inf_norm
    else:
        log.joint('ERROR: invalid phi_scale: %s\n'%(alldata['algo']['phi_scale']))

    # Cut depends on sense (because phi function does)
    suffix = namei+'_idx'+str(indmaxfeature)+'_'+str(indi)
    constrname = 'greedy_'+suffix

    if sense == '=':  # Feature is equality constraint
        gurobimodel.addConstr(Phi_L >= riskyexpr / phi_scale, name = constrname+'_plus')
        gurobimodel.addConstr(Phi_L >= -riskyexpr / phi_scale, name = constrname+'_minus')
        if loud: log.joint('cut: Phi_L >= |riksyexpr| / phi_scale\n')

    elif sense == '>':  # Feature is geq constraint
        auxvarname = 'phifunc_'+suffix  #auxvar unnecessary but helps performance (somehow)                                                                                                         
        auxvar = gurobimodel.addVar(name=auxvarname)
        slacki = nominalexpr - rhs
        gurobimodel.addConstr(auxvar == -riskyexpr - slacki, name = 'def'+auxvarname)
        gurobimodel.addConstr(Phi_L >= auxvar / phi_scale, name = constrname)  #cut is Phi_L >= max(0, phi_i(x|z)), but already have Phi_L >= 0
        if loud: log.joint('cut: phi_L >= (-riksyexpr - slacki) / phi_scale\n')

    else:  # sense == '<':  Feature is leq constraint
        auxvarname = 'phifunc_'+suffix  #auxvar unnecessary but helps performance (somehow)                                                                                              
        auxvar = gurobimodel.addVar(name=auxvarname) 
        slacki = rhs - nominalexpr
        gurobimodel.addConstr(auxvar == riskyexpr - slacki, name = 'def'+auxvarname)
        gurobimodel.addConstr(Phi_L >= auxvar / phi_scale, name = constrname)  #cut is Phi_L >= max(0, phi_i(x|z)), but already have Phi_L >= 0
        if loud: log.joint('cut: phi_L >= (riksyexpr - slacki) / phi_scale\n')

    log.joint("Added greedy cut.\n")
    return retcode, condition


def drsk_add_softmaxcuts(alldata):
    '''Adds softmax cut corresponding to Red solution: zvalues'''
    retcode = 0
    condition = ('add_softmaxcuts')
    log = alldata['log']
    structure = alldata['structure']
    set = structure['set']
    I = structure['I']
    linconstrs = alldata['LP']['linconstrs']
    quadconstrs = alldata['LP']['quadconstrs']
    gurobimodel = alldata['gurobimodel']
    iteration = alldata['algo']['iteration_cnt']

    featuredata = alldata['softmax']['features']

    solutionvectordict = alldata['solutionvectordictionary']
    zvalues = alldata['algo']['zvalues']
    alpha = alldata['softmax']['alpha']
    weight_threshold = .01  #TODO: should be parameter

    log.joint("Computing softmax cut.\n")

    # Compute pi
    pi = alldata['softmax']['pi'] = np.zeros(I)  #TODO: should be stored ahead of time
    phi_ixz = alldata['softmax']['phi_ixz']
    sum_exp = np.sum(np.exp(alpha * phi_ixz))
    np.copyto(pi, np.exp(alpha * phi_ixz) / sum_exp)

    # Construct the softmax cut
    zidx = 0
    weighted_features = []
    for i in range(I):
        # Skip features with tiny weights
        if pi[i] < weight_threshold: continue

        seti = set[i]
        name = seti['featurename']  # feature name
        numriskyi = seti['numrisky']  # number of risky coefficients in feature

        feati = featuredata[i]
        if feati['i'] != i:
            log.joint('PROBLEM: featuredata out of sync.\n')
        sense = feati['sense']
        scale = feati['scale']
        slack = feati['slack']

        # Get feature data
        if seti['isQuadratic']:  # Feature is quadratic
            qc = quadconstrs[name]
            sense = qc['sense']
            fieldLin = qc['lin']
            fieldQuad = qc['quad']
            rhs = qc['RHS']
            coeff_1norm = qc['coeff_1-norm']
        else:  # Feature is linear
            lc = linconstrs[name]  # linear constraint feature corresponds to
            sense = lc['sense']
            fieldLin = lc['field']  # dict: variable name --> (index, coefficient of term w/ variable)
            rhs = lc['RHS']
            coeff_1norm = lc['coeff_1-norm']  #for scaling displacement (i.e. impact)

        # Construct feature expression
        featexpr = gp.QuadExpr()
        for j in range(numriskyi): # for each risky coefficient
            listij = seti['list'][j]
            zvar = listij[0]  # z variable corresponsing to coefficient
            card = listij[1]  # number of x varibles in term
            arrvars = listij[2]  # x variable corresponding to coefficient

            feattermj = 0  # value of risky term at current solution
            for h in range(card): # structure
                expression = arrvars[h]  # x varible corresponding to risky coefficient
                if isinstance(expression, tuple):
                    # quadratic term
                    varname1, varname2 = expression[0], expression[1]
                    gurobivar1 = gurobimodel.getVarByName(varname1)
                    gurobivar2 = gurobimodel.getVarByName(varname2)
                    coeff = fieldQuad[expression][1]
                    feattermj += coeff*zvalues[zidx]*gurobivar1*gurobivar2
                else:
                    # linear term
                    gurobivar = gurobimodel.getVarByName(expression)  # value of x varible at current solution
                    coeff = fieldLin[expression][1]  # coefficient value
                    feattermj += coeff*zvalues[zidx]*gurobivar

            featexpr += feattermj
            zidx += 1

        # feature depends on constraint sense (=, >, <)
        if sense == '=':  # Constraint is equality constraint
            auxvar = gurobimodel.addVar(lb=0.0, name=f"phi_{i}_iter{iteration}")
            gurobimodel.addQConstr(auxvar >= featexpr / scale, name=f"abs_pos_{name}")
            gurobimodel.addQConstr(auxvar >= -featexpr / scale, name=f"abs_neg_{name}")

        elif sense == '>':  # Constraint is geq constraint
            auxvar = gurobimodel.addVar(lb=0.0, name=f"phi_{i}_iter{iteration}")
            gurobimodel.addQConstr(auxvar >= (-featexpr - slack) / scale, name=f"pospart_{name}")

        else:  # Constraint is leq constraint
            auxvar = gurobimodel.addVar(lb=0.0, name=f"phi_{i}_iter{iteration}")
            gurobimodel.addQConstr(auxvar >= (featexpr - slack) / scale, name=f"pospart_{name}")

        # Add weighted feature to list
        weighted_features.append(pi[i] * auxvar)
        log.joint(" + Adding feature %s (%s) to cut with weight %f\n"%(name, sense, pi[i]))

    # Add cut
    Phi_L = alldata['LP']['Phi_L']
    gurobimodel.addConstr(Phi_L >= gp.quicksum(weighted_features), name=f"cut_{iteration}")

    log.joint("Added softmax cut.\n")
    return retcode, condition