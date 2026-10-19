###############################################################################
# Functions for storing constraint and risk structure data using Gurobi
#
# Blake Sisson mbs2246@columbia.edu
# 10/16/2026
###############################################################################
import sys
import gurobipy as gp
from log import danoLogger
from decimal import Decimal


# =============================================================================
# STORE LP
# =============================================================================

def drsk_store_model(alldata):
    '''Store all constraints data (both linear and quadratic) for LP'''
    retcode = 0
    log = alldata['log']    
    log.joint('Now storing LP data.\n')

    # Read lpfile into Gurobi
    log.joint('Reading LP into Gurobi %s.\n' % alldata['LPFILE'])
    alldata['prob_data']['gurobimodel'] = gp.read(alldata['LPFILE'])
    log.joint('Done reading LP into Gurobi.\n')

    # Store linear constraints
    retcode = drsk_storelinearconstraints(alldata)
    log.joint('Stored linear constraints with code %d.\n' %retcode)
    if retcode != 0: return retcode  

    # Store quadratic constraints
    retcode  = drsk_storequadconstraints(alldata)
    log.joint('Quad constraints read with code %d.\n'%retcode) 
    if retcode != 0: return retcode


def drsk_storequadconstraints(alldata):
    '''Store all data for quadratic constraints'''
    retcode = 0
    log = alldata['log']
    loud = alldata['loud']
    gurobimodel = alldata['prob_data']['gurobimodel']

    Qconstrs = gurobimodel.getQConstrs()
    quadconstrs = alldata['prob_data']['all_constr_data']
    log.joint('Storing quadratic constraints; %d in total.\n'%(gurobimodel.NumQConstrs))

    # Store structure data as we go
    structure = alldata['struct_data']

    for Qconstr in Qconstrs:
        therow = gurobimodel.getQCRow(Qconstr)
        qc = quadconstrs[Qconstr.QCName] = {}
        qc['degree'] = 2
        qc['sense'] = Qconstr.QCSense
        qc['RHS'] = Qconstr.QCRHS
        qc['coeff_1-norm'] = 0.0
        qc['coeff_inf-norm'] = 0.0
        qc['isfeature'] = 0  # Record if this constraint has a risky term

        # First read the linear terms
        linQc  = therow.getLinExpr()
        qc['lin_terms'] = {}
        for j in range(linQc.size()):
            varname = linQc.getVar(j).varname
            coeff = linQc.getCoeff(j) 
            qc['lin_terms'][varname] = coeff

            # Update norms
            qc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > qc['coeff_inf-norm']: qc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than decimal_risk_thresh decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= alldata['struct_data']['decimal_risk_thresh']:
                qc['isfeature'] = 1
                riskycoeff_dict = structure['risky_coeffs'].get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary

                    if riskycoeff_dict['instances'].get(Qconstr.QCName):
                        # Coefficient already present in this constraint
                        riskycoeff_dict['instances'][Qconstr.QCName].append(('linear', varname))
                    else:
                        # First instance of coefficient in this constraint
                        riskycoeff_dict['instances'][Qconstr.QCName] = [('linear', varname)]

                else:
                    # First instance of this coefficient
                    riskycoeff_dict = structure['risky_coeffs'][coeff] = {}
                    riskycoeff_dict['index'] = index = structure['num_unique']
                    riskycoeff_dict['zvar'] = 'z_' + str(index)
                    riskycoeff_dict['instances'] = {}
                    riskycoeff_dict['instances'][Qconstr.QCName] = [('linear', varname)]
                    structure['num_unique'] += 1
                if loud: log.joint('    + coeff %g of var %s in constr %s is deemed risky\n'%(coeff, varname, Qconstr.QCName))
        
        # Next read the quadratic terms
        quadQc = therow - linQc
        qc['quad_terms'] = {}
        for j in range(quadQc.size()):
            v1 = quadQc.getVar1(j)
            v1name = v1.varname 
            v2 = quadQc.getVar2(j)
            v2name = v2.varname 
            coeff = quadQc.getCoeff(j) 
            qc['quad_terms'][(v1name, v2name)] = coeff

            # Update norms
            qc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > qc['coeff_inf-norm']: qc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than decimal_risk_thresh decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= alldata['struct_data']['decimal_risk_thresh']:
                qc['isfeature'] = 1
                riskycoeff_dict = structure['risky_coeffs'].get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary
                    
                    if riskycoeff_dict['instances'].get(Qconstr.QCName):
                        # Coefficient already present in this constraint
                        riskycoeff_dict['instances'][Qconstr.QCName].append(('quad', (v1name, v2name)))
                    else:
                        # First instance of coefficient in this constraint
                        riskycoeff_dict['instances'][Qconstr.QCName] = [('quad', (v1name, v2name))]

                else:
                    # First instance of this coefficient
                    riskycoeff_dict = structure['risky_coeffs'][coeff] = {}
                    riskycoeff_dict['index'] = index = structure['num_unique']
                    riskycoeff_dict['zvar'] = 'z_' + str(index)
                    riskycoeff_dict['instances'] = {}
                    riskycoeff_dict['instances'][Qconstr.QCName] = [('quad', (v1name, v2name))]
                    structure['num_unique'] += 1
                if loud: log.joint('    + coeff %g of var (%s,%s) in constr %s is deemed risky\n'%(coeff, v1name, v2name, Qconstr.QCName))        
        
        # Finally get constant
        qc['constant'] = linQc.getConstant()

        # Update number of feature, add 1 if this constraint was risky
        if qc['isfeature']:
            structure['numfeats'] += 1
            alldata['struct_data']['features'].append(Qconstr.QCName)

        if loud: log.joint('  - Read constraint %s. Feature=%d. Sense=%s. RHS=%g. inf-norm=%g. 1-norm=%g.\n'%(Qconstr.QCName, qc['isfeature'], qc['sense'], qc['RHS'], qc['coeff_inf-norm'], qc['coeff_1-norm']))

    return retcode 


def drsk_storelinearconstraints(alldata, loud=False):
    '''Store all data for linear constraints'''
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['prob_data']['gurobimodel']

    constrs = gurobimodel.getConstrs()
    linconstrs = alldata['prob_data']['all_constr_data']
    log.joint('Storing linear constraints; %d in total.\n'%(gurobimodel.NumConstrs))

    # Store structure data as we go
    structure = alldata['struct_data']

    for constr in constrs:
        lhs = gurobimodel.getRow(constr)
        lc = linconstrs[constr.constrName] = {}
        lc['degree'] = 1
        lc['sense'] = constr.Sense
        lc['RHS'] = constr.RHS
        lc['coeff_1-norm'] = 0.0
        lc['coeff_inf-norm'] = 0.0
        lc['constant'] = lhs.getConstant()
        lc['isfeature'] = 0  # Record if this constraint has a risky term

        # Loop through terms
        lc['lin_terms'] = {}
        lc['quad_terms'] = {}  # initialized but empty
        for j in range(lhs.size()):
            varname = lhs.getVar(j).varname
            coeff = lhs.getCoeff(j)
            lc['lin_terms'][varname] = coeff

            # Update norms
            lc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > lc['coeff_inf-norm']: lc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than decimal_risk_thresh decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= alldata['struct_data']['decimal_risk_thresh']:
                lc['isfeature'] = 1
                riskycoeff_dict = structure['risky_coeffs'].get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary

                    if riskycoeff_dict['instances'].get(constr.constrName):
                        # Coefficient already present in this constraint
                        riskycoeff_dict['instances'][constr.constrName].append(('linear', varname))
                    else:
                        # First instance of coefficient in this constraint
                        riskycoeff_dict['instances'][constr.constrName] = [('linear', varname)]

                else:
                    # First instance of this coefficient
                    riskycoeff_dict = structure['risky_coeffs'][coeff] = {}
                    riskycoeff_dict['index'] = index = structure['num_unique']
                    riskycoeff_dict['zvar'] = 'z_' + str(index)
                    riskycoeff_dict['instances'] = {}
                    riskycoeff_dict['instances'][constr.constrName] = [('linear', varname)]
                    structure['num_unique'] += 1

                if loud: log.joint('    + coeff %g of var %s in constr %s is deemed risky\n'%(coeff, varname, constr.constrName))

        # Update number of feature, add 1 if this constraint was risky
        if lc['isfeature']:
            structure['numfeats'] += 1
            alldata['struct_data']['features'].append(constr.constrName)

        if loud: log.joint('  - Read constraint %s. Feature=%d. Sense=%s. RHS=%g. inf-norm=%g. 1-norm=%g.\n'%(constr.constrName, lc['isfeature'], lc['sense'], lc['RHS'], lc['coeff_inf-norm'], lc['coeff_1-norm']))

    #breakexit('stored linear constraints and implicit structure.')
    return retcode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('usage: riskycoefficients.py LPfile')

    alldata = {}
    alldata['LPFILE'] = sys.argv[1]
    log = alldata['log'] = danoLogger('riskycoefficients.log')
    alldata['loud'] = True

    drsk_store_model(alldata)

    # log.joint("\nRisky coefficient statistics:\n")
    # log.joint(" num risky constraints = %d\n"%alldata['structure']['I'])
    # log.joint(" num unique risky terms = %d\n"%len(alldata['structure']['riskycoeffs']))
    # log.joint(" unique coefficients:\n")
    # coeff_list = list(alldata['structure']['riskycoeffs'])
    # coeff_list.sort()
    # print(coeff_list)
    # for coeff in coeff_list:
    #     coeff_dict = alldata['structure']['riskycoeffs'][coeff]
    #     log.joint("  %g appears %d times\n"%(coeff, len(coeff_dict['instances'])))