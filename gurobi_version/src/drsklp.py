import sys
import time
import math
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from myutils import breakexit


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

def drsk_storelp(alldata, getstruct=False, loud=False):
    '''Store all constraints data (both linear and quadratic) for LP'''
    retcode = 0
    log = alldata['log']    
    log.joint('Now storing LP data.\n\n')

    alldata['LP'] = {}

    '''
    retcode, maxbndinf, maxbndinfname, varbndinf = drsk_checkvariables(alldata)
    log.joint('Variables read with code %d. '%retcode)
    if retcode != 0: return retcode
    log.joint('Max bound inf %.6e at %s.\n\n'%(maxbndinf, maxbndinfname))
    '''

    if getstruct:
        log.joint('Reading implicit structure.\n')
        impl_structure = alldata['implicitstructure'] = {}
        impl_structure['I'] = 0
        impl_structure['style'] = '0-norm_per'
        impl_structure['set'] = {}
 
    retcode = drsk_storelinearconstraints(alldata, getstruct, loud)
    log.joint('Stored linear constraints with code %d.\n' %retcode)
    if retcode != 0: return retcode  
 
    retcode  = drsk_storequadconstraints(alldata, getstruct, loud)
    log.joint('Quad constraints read with code %d.\n'%retcode) 

    return retcode
 
def drsk_storequadconstraints(alldata, getstruct=False, loud=False):
    '''Store all data for quadratic constraints'''
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['gurobimodel'] 
    log.joint('Storing quadratic constraints; %d in total.\n'%(gurobimodel.NumQConstrs))
    Qconstrs = gurobimodel.getQConstrs()
    quadconstrs = alldata['LP']['quadconstrs'] = {}

    # Store implicit structure data
    if getstruct:
        impl_structure = alldata['implicitstructure']
        riskyfeat_num = impl_structure['I']

    for Qconstr in Qconstrs:
        therow = gurobimodel.getQCRow(Qconstr) 

        qc = quadconstrs[Qconstr.QCName] = {}
        qc['object'] = Qconstr
        qc['sense'] = Qconstr.QCSense
        qc['RHS'] = Qconstr.QCRHS
        qc['coeff_1-norm'] = 0.0
        qc['inf_norm'] = 0.0

        # Store implicit structure data
        if getstruct:
            numrisky = 0
            riskydict = {}

        linQc  = therow.getLinExpr()
        qc['lin'] = {}
        for j in range(linQc.size()):
            varname = linQc.getVar(j).varname
            coeff = linQc.getCoeff(j) 
            qc['lin'][varname] = (j,coeff)

            # accumulate 1-norm
            qc['coeff_1-norm'] += abs(coeff)

            # track infinity norm
            if abs(coeff) > qc['inf_norm']: qc['inf_norm'] = abs(coeff)

            if getstruct and coeff != 1.0 and coeff != -1.0 and coeff != 2.0 and coeff != -2.0:  #TODO: skip logical constraints somehow
                # Store implicit structure data
                zvar = 'z_'+str(riskyfeat_num)+'_lin'+str(j)
                card = 1
                arrvars = []
                arrvars.append(varname)
                riskydict[numrisky] = (zvar, card, arrvars)
                numrisky += 1
                if loud: log.joint('+ coeff %g of var %s (idx %d) in constr %s (idx %d) is deemed risky\n'%(coeff, varname, j, Qconstr.QCName, riskyfeat_num))
        
        quadQc = therow - linQc
        qc['quad'] = {}
        for j in range(quadQc.size()):
            v1 = quadQc.getVar1(j)
            v1name = v1.varname 
            v2 = quadQc.getVar2(j)
            v2name = v2.varname 
            coeff = quadQc.getCoeff(j) 
            qc['quad'][(v1name,v2name)] = (j,coeff)

            # accumulate 1-norm
            qc['coeff_1-norm'] += abs(coeff)

            # track infinity norm
            if abs(coeff) > qc['inf_norm']: qc['inf_norm'] = abs(coeff)

            if getstruct and coeff != 1.0 and coeff != -1.0 and coeff != 2.0 and coeff != -2.0:  #skip logical constraints somehow
                # Store implicit structure data
                zvar = 'z_'+str(riskyfeat_num)+'_quad'+str(j)
                card = 1
                arrvars = []
                arrvars.append((v1name, v2name))
                riskydict[linQc.size() + numrisky] = (zvar, card, arrvars)
                numrisky += 1
                if loud: log.joint('+ coeff %g of var (%s,%s) (idx %d) in constr %s (idx %d) is deemed risky\n'%(coeff, v1name, v2name, j, Qconstr.QCName, riskyfeat_num))

        qc['constant'] = linQc.getConstant()

        # Store implicit structure data
        if getstruct and numrisky > 0:  #only store feature if risky coefficients present
            impl_structure['set'][riskyfeat_num] = {}
            impl_structure['set'][riskyfeat_num]['featurename'] = Qconstr.QCName
            impl_structure['set'][riskyfeat_num]['list'] = riskydict
            impl_structure['set'][riskyfeat_num]['numrisky'] = numrisky
            impl_structure['set'][riskyfeat_num]['isQuadratic'] = True
            riskyfeat_num += 1
        
    # Store implicit structure data
    if getstruct:
        impl_structure['I'] = riskyfeat_num

    return retcode 

def drsk_storelinearconstraints(alldata, getstruct=False, loud=False):
    '''Store all data for linear constraints'''
    retcode = 0
    log = alldata['log']
    loud = alldata['LOUDCONSTRAINTS']
    gurobimodel = alldata['gurobimodel']  
    log.joint('Storing linear constraints; %d in total.\n'%(gurobimodel.NumConstrs))
    constrs = gurobimodel.getConstrs()
    linconstrs = alldata['LP']['linconstrs'] = {}

    # Store implicit structure data
    if getstruct:
        impl_structure = alldata['implicitstructure']
        riskyfeat_num = impl_structure['I']

    for constr in constrs:
        lhs = gurobimodel.getRow(constr)

        lc = linconstrs[constr.constrName] = {}
        lc['field'] = {}
        lc['object'] = constr
        lc['constant'] = lhs.getConstant()
        lc['sense'] = constr.Sense
        lc['RHS'] = constr.RHS
        lc['coeff_1-norm'] = 0.0
        lc['inf_norm'] = 0.0

        # Store implicit structure data
        if getstruct:
            numrisky = 0
            riskydict = {}
 
        if loud: log.joint('\nStarting with constraint %s\n' %(constr.constrName))
        for j in range(lhs.size()):
            varname = lhs.getVar(j).varname
            coeff = lhs.getCoeff(j)
            lc['field'][varname] = (j,coeff)

            # accumulate 1-norm
            lc['coeff_1-norm'] += abs(coeff)

            # track infinity norm
            if abs(coeff) > lc['inf_norm']: lc['inf_norm'] = abs(coeff) 

            if getstruct and coeff != 1.0 and coeff != -1.0 and coeff != 2.0 and coeff != -2.0:  #skip logical constraints somehow
                # Store implicit structure data
                zvar = 'z_'+str(riskyfeat_num)+'_'+str(j)
                card = 1
                arrvars = []
                arrvars.append(varname)
                riskydict[numrisky] = (zvar, card, arrvars)
                numrisky += 1
                if loud: log.joint('+ coeff %g of var %s (idx %d) in constr %s (idx %d) is deemed risky\n'%(coeff, varname, j, constr.constrName, riskyfeat_num))

        # Store implicit structure data
        if getstruct and numrisky > 0:  #only store feature if risky coefficients present
            impl_structure['set'][riskyfeat_num] = {}
            impl_structure['set'][riskyfeat_num]['featurename'] = constr.constrName
            impl_structure['set'][riskyfeat_num]['list'] = riskydict
            impl_structure['set'][riskyfeat_num]['numrisky'] = numrisky
            impl_structure['set'][riskyfeat_num]['isQuadratic'] = False
            riskyfeat_num += 1

    # Store implicit structure data
    if getstruct:
        impl_structure['I'] = riskyfeat_num

    #breakexit('stored linear constraints and implicit structure.')
    return retcode


# =============================================================================
# CHECK SOLUTION
# =============================================================================

def drsk_checksolution(alldata):
    retcode = 0
    log = alldata['log']    
    log.joint('Now checking solution.\n\n')

    retcode, maxbndinf, maxbndinfname, varbndinf = drsk_checkvariables(alldata)
    log.joint('Variables checked with code %d. '%retcode)
    if retcode != 0: return retcode
    log.joint('Max bound inf %.6e at %s.\n\n'%(maxbndinf, maxbndinfname))

    linconstrtol = 1e-4
    retcode, maxlinconstrinf, maxlinconstrname, constrinf = drsk_checklinearconstraints(alldata, linconstrtol)
    log.joint('Linear constraints checked with code %d.\n'%retcode)
    if retcode != 0: return retcode    
    log.joint('Max linconstr inf %.6e at %s.\n\n'%(maxlinconstrinf, maxlinconstrname))    

    quadconstrtol = 1e-4
    retcode, maxquadconstrinf, maxquadconstrname, quadconstrinf = drsk_checkquadconstraints(alldata, quadconstrtol)
    log.joint('Quad constraints checked with code %d.\n'%retcode)
    if retcode != 0: return retcode    
    log.joint('Max quadconstr inf %.6e at %s.\n\n'%(maxquadconstrinf, maxquadconstrname))

    return retcode

def drsk_checkquadconstraints(alldata, quadconstrtol):
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['gurobimodel']
    solutionvectordictionary = alldata['solutionvectordictionary']

    maxquadconstrinf = -1
    maxquadconstrname = None
    quadconstrinf = {}
    
    log.joint('Checking quadratic constraints; %d in total.\n'%(gurobimodel.NumQConstrs))
    Qconstrs = gurobimodel.getQConstrs()
    for Qconstr in Qconstrs:
        therow = gurobimodel.getQCRow(Qconstr)
        #log.joint(Qconstr.QCName+ ' ' + Qconstr.QCSense + ' ' + str(Qconstr.QCRHS) + '\n')
        linQc  = therow.getLinExpr()

        linterm = 0
        for j in range(linQc.size()):
            varname = linQc.getVar(j).varname
            coeff = linQc.getCoeff(j)
            varvalue = solutionvectordictionary[varname]
            linterm += coeff*varvalue
        
        quadQc = therow - linQc
    
        quadterm = 0
        for j in range(quadQc.size()):
            v1 = quadQc.getVar1(j)
            v1name = v1.varname
            varvalue1 = solutionvectordictionary[v1name]
            v2 = quadQc.getVar2(j)
            v2name = v2.varname
            varvalue2 = solutionvectordictionary[v2name]
            coeff = quadQc.getCoeff(j)
            quadterm += coeff*varvalue1*varvalue2

        constant = linQc.getConstant()
        lhstotal = linterm + quadterm + constant
        #log.joint('linear term = %.3e, quadterm = %.3e; total = %.3e\n'%(linterm, quadterm, lhstotal))

        rhs = Qconstr.QCRHS

        if Qconstr.QCSense == '<':
            thisinf = lhstotal - rhs
        elif Qconstr.QCSense == '>':
            thisinf = rhs - lhstotal
        else:
            thisinf = abs(rhs - lhstotal)

        thisinf = max(0, thisinf)

        if thisinf > maxquadconstrinf:
            maxquadconstrinf = thisinf
            maxquadconstrname = Qconstr.QCName
            quadconstrinf[Qconstr.QCName] = thisinf
        
        if thisinf > quadconstrtol:
            log.joint('%s (%d lin nonz, % quad nonz %d) %s %f: thisinf %f\n'%(Qconstr.QCName, linQc.size(), quadQc.size(), Qconstr.QCSense,Qconstr.QCRHS, thisinf))
            #breakexit('poo')
            retcode = 1

    return retcode, maxquadconstrinf, maxquadconstrname, quadconstrinf

def drsk_checklinearconstraints(alldata, linconstrtol):
    retcode = 0
    log = alldata['log']
    gurobimodel = alldata['gurobimodel']
    solutionvectordictionary = alldata['solutionvectordictionary']    
    log.joint('Checking linear constraints; %d in total.\n'%(gurobimodel.NumConstrs))
    constrs = gurobimodel.getConstrs()

    maxlinconstrinf = -1
    maxlinconstrname = None
    linconstrinf = {}

    loud = alldata['LOUDCONSTRAINTS']

    thresh = 1e-8
    
    for constr in constrs:
        lhs = gurobimodel.getRow(constr)

        lhsval = 0
        #print('\n')
        if loud: log.joint('\nStarting with constraint %s\n' %(constr.constrName))
        for j in range(lhs.size()):
            varname = lhs.getVar(j).varname
            coeff = lhs.getCoeff(j)
            varvalue = solutionvectordictionary[varname]
            lhsval += coeff*varvalue
            if loud and np.abs(coeff*varvalue) > thresh:
                log.joint("%s c %g x %g lhs %g\n" %(varname, coeff, varvalue, lhsval))
            #print(varname, 'coeff', coeff, 'varvalue', varvalue, lhsval)

        if loud: log.joint('Total LHS: %g\n' %(lhsval))
        constant = lhs.getConstant()
        lhsval += constant

        if constr.Sense == '<':
            thisinf = lhsval - constr.RHS
        elif constr.Sense == '>':
            thisinf = constr.RHS - lhsval
        else:
            thisinf = abs(constr.RHS - lhsval)

        thisinf = max(0, thisinf)

        if thisinf > maxlinconstrinf:
            maxlinconstrinf = thisinf
            maxlinconstrname = constr.ConstrName
            linconstrinf[constr.ConstrName] = thisinf

        if thisinf > linconstrtol:
            log.joint('%s (%d lin nonz, const = %f) %s %f: thisinf %f\n'%(constr.ConstrName, lhs.size(), lhs.getConstant(), constr.Sense, constr.RHS, thisinf))
                
            #breakexit('poo')
            retcode = 1

        linconstrinf[constr.ConstrName] = thisinf

    return retcode, maxlinconstrinf, maxlinconstrname, linconstrinf

def drsk_checkvariables(alldata):
    retcode = 0
    log = alldata['log']    
    log.joint('Checking variables.\n')

    maxbndinf = -1
    maxbndinfname = None
    varbndinf = {}

    gurobimodel = alldata['gurobimodel']
    if 'solutionvectordictionary' not in alldata.keys():
        log.joint('Error. \'solutionvectordictionary\' must be read in\n')
        retcode = 1
        return retcode, maxbndinf, maxbndinfname, varbndinf

    count_in_solution = {}    
    for var in gurobimodel.getVars():
        count_in_solution[var.varname] = 0

    solutionvectordictionary = alldata['solutionvectordictionary']
    insolnotingurobimodel = alldata['insolnotingurobimodel']
    #insolnotingurobimodelcnt = alldata['insolnotingurobimodelcnt']
    nonzerosinsol = alldata['NONZEROSINSOL']

    #print(solutionvectordictionary)

    for varname in solutionvectordictionary:
        varvalue = solutionvectordictionary[varname]        
        if varname not in count_in_solution and varname not in insolnotingurobimodel.values():
            log.joint("!!!! %s weird variable\n"%(varname))
            print(insolnotingurobimodel)
            sys.exit('hoooo')
        #if varname in insolnotingurobimodel.values() and nonzerosinsol:
        #    count_in_solution[varname] = 0
    
    for varname in solutionvectordictionary:
        #print(varname)
        if varname not in count_in_solution: #i.e., a variable in the LP but not in the solution        
            log.joint('Error: variable %s in solution is not in gurobimodel\n'%(varname))
            retcode = 1
            return retcode, maxbndinf, maxbndinfname, varbndinf
        varvalue = solutionvectordictionary[varname]        
        if count_in_solution[varname] > 0:
            log.joint('Error: variable %s appears multiple times in solution\n'%(varname))            
            retcode = 1
            return retcode, maxbndinf, maxbndinfname, varbndinf
        count_in_solution[varname] = 1

    j = 0
    nonzerosinsol = alldata['NONZEROSINSOL']
    strict = (nonzerosinsol == 0)
    countnotseen = 0
    for var in gurobimodel.getVars():
        varname = var.varname
        #print('--->',j, var.varname, count_in_solution[var.varname])
        j += 1
        #if varname != 'objvar' and varname != 'constant' and varname != 'qcostvar' and count_in_solution[var.varname] == 0:
        if count_in_solution[varname] == 0:
            if strict:        
                log.joint('Error: variable %s in gurobimodel is not in solution\n'%(varname))
                retcode = 1
                return retcode, maxbndinf, maxbndinfname, varbndinf
            else:
                # in this case a variable not in the solution is to be set to zero
                solutionvectordictionary[varname] = 0
                if countnotseen == 0:
                    log.joint('Warning: variable %s in gurobimodel is not in solution.\n'%(varname))
                    log.joint('Warnings will be not repeated.\n')

                countnotseen += 1
                count_in_solution[varname] = 1

    if countnotseen > 0: log.joint('%d variables in gurobimodel but not in solution.\n' %(countnotseen))
    for var in gurobimodel.getVars():

        value = solutionvectordictionary[var.varname]

        ubinf = lbinf = 0

        if var.ub < gp.GRB.INFINITY:
            ubinf = max(0, value - var.ub)
        if var.lb > -gp.GRB.INFINITY:
            lbinf = max(0, value - var.ub)
        thisinf = max(ubinf, lbinf)
        
        #print(var.varname,'value',value,'lb',var.lb,'ub',var.ub)        
        #print('lbinf',lbinf, 'ubinf',ubinf)

        varbndinf[var.varname] = thisinf

        if thisinf > maxbndinf:
            maxbndinf = thisinf
            maxbndinfname = var.varname
            
            #print(maxbndinf, maxbndinfname)
            #breakexit('poo')

    breakexit('Checked variables.')
    return retcode, maxbndinf, maxbndinfname, varbndinf


# =============================================================================
# WRITING TO FILE
# =============================================================================

def drsk_writeLP(alldata):
    log = alldata['log']
    iteration = alldata['algo']['iteration_cnt']

    filename = 'form_'+str(iteration)+'.lp'

    log.joint('Writing LP to file %s.\n' %(filename))
    
    gurobimodel = alldata['gurobimodel']
    gurobimodel.write(filename)


def drsk_writeStructure(alldata, structure, filename=None):
    log = alldata['log']

    if filename is None:
        lpname = alldata['LPFILE'].split('/')[-1].split('.')[0]
        filename = 'structimpl_'+lpname+'.conf'
    fwriter = open(filename, 'w')

    log.joint('Writing structure to file %s.\n' %(filename))
    
    fwriter.write('I = %d budget = %g style = %s\n'%(structure['I'], structure['budget'], structure['style']))
    for seti in structure['set']:
        fwriter.write('%s : numrisky %d '%(seti['featurename'], seti['numrisky']))
        ind = 0
        for listij in seti['list']:
            fwriter.write('ind %d %s %d %s'%(listij[0], listij[1], listij[2]))
            ind += 1
        fwriter.write('\n')

    fwriter.write('END\n')

def drsk_writeSol(alldata, solution, filename=None):
    log = alldata['log']
    model = alldata['gurobimodel']
    solutionvectordictionary = alldata['solutionvectordictionary']

    if filename is None:
        iteration = alldata['algo']['iteration_cnt']
        filename = 'form_'+str(iteration)+'.sol'
    fwriter = open(filename, 'w')

    log.joint('Writing solution to file %s.\n' %(filename))

    for v in model.getVars():
        x = solution[v.varname]
        if math.fabs(x) > 0.00000001:
            fwriter.write('%s = %.16e\n'%(v.varname, x))

    fwriter.write('END\n')


# =============================================================================
# SOLVE LP
# =============================================================================

def drsk_solveLP(alldata, timelimit=60):
    log = alldata['log']
    model = alldata['gurobimodel']
    solutionvectordictionary = alldata['solutionvectordictionary']

    log.joint('Solving Model\n')
    log.joint("  variables = " + str(model.NumVars) + "\n")
    log.joint("  constraints = " + str(model.NumConstrs) + "\n")

    # Solve LP
    model.setParam('Method', 2)
    model.setParam("TimeLimit", timelimit)
    t0 = time.time()
    model.optimize()
    t1 = time.time()
    runtime = t1 - t0

    retcode = 1
    stringvalue = 'none'
    success = False

    # log results
    if model.status == GRB.status.INF_OR_UNBD:
        log.joint('->LP infeasible or unbounded\n')
        stringvalue = 'INFEASIBLE OR UNBOUNDED'
        model.Params.DualReductions = 0
        t0p = time.time()
        model.optimize()
        t1p = time.time()
        runtime += t1p - t0p

    if model.status == GRB.status.INFEASIBLE:
        log.joint('->LP infeasible\n')
        stringvalue = 'INFEASIBLE'
        model.computeIIS()
        model.write("model.ilp")
            
    elif model.status == GRB.status.UNBOUNDED:
        log.joint('->LP unbounded\n')
        stringvalue = 'UNBOUNDED'

    elif model.status == GRB.OPTIMAL:
        log.joint(' OPTIMAL. optimal value: {:.4e} in time {:.4e}\n'.format(model.objval, t1-t0))
        success = True
        stringvalue = 'OPTIMAL'

    elif model.status == GRB.SUBOPTIMAL:
        log.joint(' SUBOPTIMAL. (sub)optimal value: {:.4e} in time {:.4e}\n'.format(model.objval, t1-t0))
        success = True
        stringvalue = 'SUBOPTIMAL'

    else:
        log.joint(' unexpected status ' + str(model.status) + '\n')
        stringvalue = 'UNEXPECTED'

    # Store and log solution
    if success:
        retcode = 0
        log.joint('Optimal objective = %g\n' % model.objVal)
        log.joint('Optimal variable values:\n')
        count = 0
        for v in model.getVars():
            # Store soltuion
            solutionvectordictionary[v.varname] = v.x

            # Log nonzero values
            if math.fabs(v.x) > 0.00000001:
                log.joint('%s = %g\n'%(v.varname,v.x))
                count += 1

        log.joint(str(count) + " nonzero variables in solution\n")

    #breakexit('solved LP')
    return retcode, stringvalue


# =============================================================================
# EVALUATE OBJECTIVE
# =============================================================================

def drsk_getobjectivevalue(alldata, solutionvectordictionary, loud):
    log = alldata['log']
    gurobimodel = alldata['gurobimodel']
    obj = gurobimodel.getObjective()

    if isinstance(obj, gp.QuadExpr):
        if loud: log.joint('\n->quadratic objective!\n')
        objisquad = True
        lin_obj = obj.getLinExpr()
        q_obj = obj - lin_obj
    else:
        if loud: log.joint('\n->Linear objective!\n')        
        objisquad = False
        lin_obj = obj

    quadterm = 0
    if objisquad:
        for j in range(q_obj.size()):
            v1name = q_obj.getVar1(j).varname
            v2name = q_obj.getVar2(j).varname
            coeff = q_obj.getCoeff(j)
            thisterm = coeff*solutionvectordictionary[v1name]*solutionvectordictionary[v2name]
            #print(coeff, v1name, solutionvectordictionary[v1name], v2name, solutionvectordictionary[v2name], thisterm)
            quadterm += thisterm

    linterm = 0
    linterm_noPhi = 0
    for j in range(lin_obj.size()):
        varname = lin_obj.getVar(j).varname
        coeff = lin_obj.getCoeff(j)
        linterm += coeff*solutionvectordictionary[varname]
        if varname != 'Phi_L':
            linterm_noPhi += coeff*solutionvectordictionary[varname]
            #print(varname, coeff, solutionvectordictionary[varname])

    constant = lin_obj.getConstant()
    total = quadterm + linterm + constant
    total_noPhi = quadterm + linterm_noPhi + constant
    if loud: log.joint('Iter %d Quad term %.4e lin term %.4e constant %.4e total %.6e.\n' %(alldata['algo']['iteration_cnt'],quadterm, linterm, constant, total))

    return total, total_noPhi