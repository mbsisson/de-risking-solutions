# Sandbox for drsklp.py
# Test file for reading lp and storing risky coefficients,
# possibly with single coefficient appearing multiple constraints

import sys
import gurobipy as gp

################################################
# Necessary for scripts in src/sandbox/
from pathlib import Path
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))
################################################

from log import danoLogger
from decimal import Decimal
from myutils import breakexit

RISKY_DECIMAL_THRESH = 3  #TODO: should be parameter

# =============================================================================
# READ LP
# =============================================================================

def drsk_getlp(alldata):
    '''Read lp file into gurobimodel'''
    log = alldata['log']

    log.joint('Reading LP %s.\n' % alldata['LPFILE'])

    gurobimodel = gp.read(alldata['LPFILE'])
    alldata['gurobimodel'] = gurobimodel

    log.joint("Number of variables = " + str(gurobimodel.NumVars)+'.\n')

    alldata['n'] = gurobimodel.NumVars

    log.joint('Done reading LP.\n')


# =============================================================================
# STORE LP
# =============================================================================

def drsk_storelp(alldata):
    '''Store all constraints data (both linear and quadratic) for LP'''
    retcode = 0
    log = alldata['log']    
    log.joint('Now storing LP data.\n\n')
    loud = alldata['loud']

    alldata['LP'] = {}

    structure = alldata['structure'] = {}
    structure['I'] = 0
    structure['style'] = '0-norm_per'
    structure['riskycoeffs'] = {}
    structure['num_uniqueriskycoeffs'] = 0
 
    retcode = drsk_storelinearconstraints(alldata, loud)
    log.joint('Stored linear constraints with code %d.\n' %retcode)
    if retcode != 0: return retcode  
 
    retcode  = drsk_storequadconstraints(alldata, loud)
    log.joint('Quad constraints read with code %d.\n'%retcode) 
    if retcode != 0: return retcode
 
def drsk_storequadconstraints(alldata, loud=False):
    '''Store all data for quadratic constraints'''
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['gurobimodel']
    Qconstrs = gurobimodel.getQConstrs()
    quadconstrs = alldata['LP']['quadconstrs'] = {}
    log.joint('Storing quadratic constraints; %d in total.\n'%(gurobimodel.NumQConstrs))

    # Store structure data as we go
    structure = alldata['structure']
    riskycoeffs_dict = structure['riskycoeffs']

    for Qconstr in Qconstrs:
        therow = gurobimodel.getQCRow(Qconstr)
        qc = quadconstrs[Qconstr.QCName] = {}
        qc['object'] = Qconstr
        qc['sense'] = Qconstr.QCSense
        qc['RHS'] = Qconstr.QCRHS
        qc['coeff_1-norm'] = 0.0
        qc['coeff_inf-norm'] = 0.0

        # Record if this constraint has a risky term
        riskyconstr_flag = 0

        # First read the linear terms
        linQc  = therow.getLinExpr()
        qc['lin_terms'] = {}
        for j in range(linQc.size()):
            varname = linQc.getVar(j).varname
            coeff = linQc.getCoeff(j) 
            qc['lin_terms'][varname] = (j,coeff)

            # Update norms
            qc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > qc['coeff_inf-norm']: qc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than RISKY_DECIMAL_THRESH decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= RISKY_DECIMAL_THRESH:
                riskyconstr_flag = 1
                riskycoeff_dict = riskycoeffs_dict.get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary
                    riskycoeff_dict['instances'].append(('quadconstr', Qconstr.QCName, varname, j))
                else:
                    # First instance of this coefficient
                    riskycoeffs_dict[coeff] = {}
                    riskycoeffs_dict[coeff]['index'] = structure['num_uniqueriskycoeffs']
                    riskycoeffs_dict[coeff]['zvar'] = 'z_' + str(riskycoeffs_dict[coeff]['index'])
                    riskycoeffs_dict[coeff]['instances'] = [('quadconstr', Qconstr.QCName, varname, j)]
                    structure['num_uniqueriskycoeffs'] += 1
                if loud: log.joint('+ coeff %g of var %s in constr %s is deemed risky\n'%(coeff, varname, Qconstr.QCName))
        
        # Next read the quadratic terms
        quadQc = therow - linQc
        qc['quad_terms'] = {}
        for j in range(quadQc.size()):
            v1 = quadQc.getVar1(j)
            v1name = v1.varname 
            v2 = quadQc.getVar2(j)
            v2name = v2.varname 
            coeff = quadQc.getCoeff(j) 
            qc['quad_terms'][(v1name,v2name)] = (j,coeff)

            # Update norms
            qc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > qc['coeff_inf-norm']: qc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than RISKY_DECIMAL_THRESH decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= RISKY_DECIMAL_THRESH:
                riskyconstr_flag = 1
                riskycoeff_dict = riskycoeffs_dict.get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary
                    riskycoeff_dict['instances'].append(('quadconstr', Qconstr.QCName, (v1name,v2name), j))
                else:
                    # First instance of this coefficient
                    riskycoeffs_dict[coeff] = {}
                    riskycoeffs_dict[coeff]['index'] = structure['num_uniqueriskycoeffs']
                    riskycoeffs_dict[coeff]['zvar'] = 'z_' + str(riskycoeffs_dict[coeff]['index'])
                    riskycoeffs_dict[coeff]['instances'] = [('quadconstr', Qconstr.QCName, (v1name,v2name), j)]
                    structure['num_uniqueriskycoeffs'] += 1
                if loud: log.joint('+ coeff %g of var (%s,%s) in constr %s is deemed risky\n'%(coeff, v1name, v2name, Qconstr.QCName))        
        
        # Finally get constant
        qc['constant'] = linQc.getConstant()

        # Update number of feature, add 1 if this constraint was risky
        structure['I'] += riskyconstr_flag

    return retcode 

def drsk_storelinearconstraints(alldata, loud=False):
    '''Store all data for linear constraints'''
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['gurobimodel']
    constrs = gurobimodel.getConstrs()
    linconstrs = alldata['LP']['linconstrs'] = {}
    log.joint('Storing linear constraints; %d in total.\n'%(gurobimodel.NumConstrs))

    # Store structure data as we go
    structure = alldata['structure']
    riskycoeffs_dict = structure['riskycoeffs']

    for constr in constrs:
        lhs = gurobimodel.getRow(constr)
        lc = linconstrs[constr.constrName] = {}
        lc['object'] = constr
        lc['sense'] = constr.Sense
        lc['RHS'] = constr.RHS
        lc['coeff_1-norm'] = 0.0
        lc['coeff_inf-norm'] = 0.0
        lc['constant'] = lhs.getConstant()

        # Record if this constraint has a risky term
        riskyconstr_flag = 0

        # Loop through terms
        lc['lin_terms'] = {}
        for j in range(lhs.size()):
            varname = lhs.getVar(j).varname
            coeff = lhs.getCoeff(j)
            lc['lin_terms'][varname] = (j,coeff)

            # Update norms
            lc['coeff_1-norm'] += abs(coeff)
            if abs(coeff) > lc['coeff_inf-norm']: lc['coeff_inf-norm'] = abs(coeff)

            # Check if coefficient is risky, i.e., has more than RISKY_DECIMAL_THRESH decimal points
            if abs(Decimal(str(coeff)).as_tuple().exponent) >= RISKY_DECIMAL_THRESH:
                riskyconstr_flag = 1
                riskycoeff_dict = riskycoeffs_dict.get(coeff)
                if riskycoeff_dict:
                    # Coefficient already stored in riskycoeffs dictionary
                    riskycoeff_dict['instances'].append(('linconstr', constr.constrName, varname, j))
                else:
                    # First instance of this coefficient
                    riskycoeffs_dict[coeff] = {}
                    riskycoeffs_dict[coeff]['index'] = structure['num_uniqueriskycoeffs']
                    riskycoeffs_dict[coeff]['zvar'] = 'z_' + str(riskycoeffs_dict[coeff]['index'])
                    riskycoeffs_dict[coeff]['instances'] = [('linconstr', constr.constrName, varname, j)]
                    structure['num_uniqueriskycoeffs'] += 1
                if loud: log.joint('+ coeff %g of var %s in constr %s is deemed risky\n'%(coeff, varname, constr.constrName))

        # Update number of feature, add 1 if this constraint was risky
        structure['I'] += riskyconstr_flag

    #breakexit('stored linear constraints and implicit structure.')
    return retcode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('usage: riskycoefficients.py LPfile')

    alldata = {}
    alldata['LPFILE'] = sys.argv[1]
    log = alldata['log'] = danoLogger('riskycoefficients.log')
    alldata['loud'] = True

    drsk_getlp(alldata)

    drsk_storelp(alldata)

    log.joint("\nRisky coefficient statistics:\n")
    log.joint(" num risky constraints = %d\n"%alldata['structure']['I'])
    log.joint(" num unique risky terms = %d\n"%len(alldata['structure']['riskycoeffs']))
    log.joint(" unique coefficients:\n")
    coeff_list = list(alldata['structure']['riskycoeffs'])
    coeff_list.sort()
    print(coeff_list)
    for coeff in coeff_list:
        coeff_dict = alldata['structure']['riskycoeffs'][coeff]
        log.joint("  %g appears %d times\n"%(coeff, len(coeff_dict['instances'])))