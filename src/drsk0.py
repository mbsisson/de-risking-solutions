import sys
from datetime import datetime
from log import danoLogger
from myutils import breakexit
from versioner import stateversion
from drsklp import drsk_getlp, drsk_storelp
from drskalgo import drsk_greedy #drsk_softmax


def drsk_readsolution(alldata, filename):
    '''Read LP solution from file, using the gurobi model for variable names'''

    log = alldata['log']

    log.joint("Reading solution file " + filename + ".\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    solutionvectordictionary = {}
    gurobimodel = alldata['gurobimodel']
    count_in_solution = {}    
    for var in gurobimodel.getVars():
        count_in_solution[var.varname] = 0
        solutionvectordictionary[var.varname] = 0
        
    # Question: What is this? Why not used?
    readnonzeros = alldata['NONZEROSINSOL']
    '''
    if readnonzeros:
        for var in gurobimodel.getVars():
            solutionvectordictionary[var.varname] = 0
    '''
    
    # Question: why is all below necessary?
    linenum = 0
    insolnotingurobimodel = {}
    insolnotingurobimodelcnt = 0

    while linenum < len(lines):
        thisline = lines[linenum].split()

        # the check is redundant in the sense that we will repeat it

                    
        if len(thisline) > 0 and thisline[0][0] != '#':
            if thisline[0] != 'END':
                if thisline[0][0] != '/':
                    varname = thisline[0]
                    varvalue = float(thisline[2])
                    if varname not in count_in_solution:
                        log.joint('Variable %s in solution (value %g) is not in gurobimodel.\n' %(varname,varvalue)) #b.c. count = 0 for LP vars
                        #print(varname, varvalue, insolnotingurobimodelcnt)                 
                        insolnotingurobimodel[insolnotingurobimodelcnt] = varname
                        insolnotingurobimodelcnt += 1

                    else:
                        if count_in_solution[varname] > 0:
                            log.joint('Variable %s appears multiple times in solution\n' %varname)
                            return 1
                        
                    count_in_solution[varname] = 1
                    solutionvectordictionary[varname] = varvalue
                else:
                    print('Skipping', thisline)
            elif thisline[0] == 'END':
                break
        linenum += 1
    
    alldata['solutionvectordictionary'] = solutionvectordictionary
    alldata['insolnotingurobimodel'] = insolnotingurobimodel
    alldata['insolnotingurobimodelcnt'] = insolnotingurobimodelcnt
    return 0
    

def drsk_readstructure(alldata, filename):
    '''Read structure of risky coefficients''' 
    log = alldata['log']
    log.joint("Reading structure file " + filename + ".\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    thisline = lines[0].split()
    I = int( thisline[2])
    budget = float(thisline[5])
    log.joint('I = %d budget = %g\n' %(I, budget))
    linenum = 1
    structure = alldata['structure'] = {}
    structure['I'] = I
    structure['set'] = {}
    readlines = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()

        # the check may be redundant in the sense that we may repeat it
        if len(thisline) > 0 and thisline[0][0] != '#':
            if thisline[0] != 'END':
                #print(thisline)
                constrname = thisline[0]
                numrisky = int(thisline[3])
                position = 6
                structure['set'][readlines] = {}
                structure['set'][readlines]['numrisky'] = numrisky
                structure['set'][readlines]['featurename'] = constrname
                structure['set'][readlines]['list'] = {}
                structure['set'][readlines]['isQuadratic'] = False  #whether feature is a quadratic

                for j in range(numrisky):
                    #print('>',j,numrisky,thisline[position],constrname)
                    zvar = thisline[position]
                    card = int(thisline[position + 1])  # card > 1 if same risky coefficient appears >once in constraint
                    if len(thisline) < position  + card:
                        log.joint('Line %d is too short (needs %d has %d)\n' %(linenum, 4 + card, len(thisline)))
                        breakexit('bad')
                    arrvars = []
                    for h in range(card):
                        pp = position + 2 + h

                        if ',' in thisline[pp]:
                            # quadratic term
                            structure['set'][readlines]['isQuadratic'] = True
                            quadterm = thisline[pp].split(',')
                            term = (quadterm[0], quadterm[1])
                        else:
                            # linear term
                            term = thisline[pp]

                        arrvars.append(term)
                        #position += 1

                    # name of z var, cardinality of z var, list of variables risky coefficient applies to
                    structure['set'][readlines]['list'][j] = (zvar, card, arrvars)
                    position += 4 + card  

                #print(readlines,structure['set'][readlines])
                readlines += 1            
                #breakexit('pooo')
            else:
                if readlines < I:
                    print('only read %d lines; expecting %d.\n' %(readlines, I + 1))
                    breakexit('poo2')
                break
        linenum += 1

    #breakexit('readstruct')
    # now check the structure, i.e. ensure each constraint actually has the 'x' variables listed
    log.joint('Skipping structure check.\n')
    # gurobimodel = alldata['gurobimodel']    
    # set = structure['set']
    # linconstrs = alldata['LP']['linconstrs']
    # quadconstrs = alldata['LP']['quadconstrs']    
    # for i in range(I):
    #     seti = set[i]

    #     name = seti['featurename']
    #     if name not in linconstrs:
    #         log.joint('Structure %s not found among linear constraints.\n'%(filename))
    #         breakexit('bad')
    #         return 1

    #     numriskyi = seti['numrisky']
    #     for j in range(numriskyi):
    #         listij = seti['list'][j]
    #         #print('listij for i',i,'j',j, listij)
    #         zvar = listij[0]
    #         card = listij[1]
    #         arrvars = listij[2]
    #         #print(i, j, name, zvar, card, arrvars)
    #         #breakexit('arr')
    #         target = linconstrs[name]
    #         field = target['field']
    #         for k in range(card):
    #             expression = arrvars[k]
    #             if expression not in field:
    #                 log.joint('Expression %s not in field for constraint %s.\n' %(expression, name))
    #                 breakexit('bad')

    log.joint('Read structure.\n')
    return 0
    

def drsk_readparameters(alldata, filename):
    '''Read parameters from file'''
    log = alldata['log']
    log.joint("Reading parameter file " + filename + ".\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    tol = 'None'
    maxits = 'None'
    alpha = 'None'
    lambda_hi = 'None'
    lambda_lo = 'None'
    xi = 'None'
    budget = 'None'
    phi_scale = 'None'

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'tol':
                tol = float(thisline[1])
            elif word == 'maxits':
                maxits = int(thisline[1])
            elif word == 'alpha':
                alpha = float(thisline[1])
            elif word == 'lambda_hi':
                lambda_hi = float(thisline[1])
            elif word == 'lambda_lo':
                lambda_lo = float(thisline[1])
            elif word == 'xi':
                xi = float(thisline[1])
            elif word == 'budget':
                budget = float(thisline[1])
            elif word == 'phi_scale':
                phi_scale = thisline[1]
            elif word == 'theta':
                theta = float(thisline[1])
                alldata['algo'][word] = theta
                log.joint(word + ' ' + str(theta) + '\n')
            elif word == 'loud':
                loud = int(thisline[1])
                alldata[word] = loud
                log.joint(word + ' ' + str(loud) + '\n')
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + "\n")
                continue

        linenum += 1

    for x in [('tol', tol), ('maxits', maxits), ('alpha', alpha), ('lambda_hi', lambda_hi), ('lambda_lo', lambda_lo),
              ('xi', xi), ('budget', budget), ('phi_scale', phi_scale)]:
        if x[1] == 'NONE':
            log.stateandquit(' no ' + x[0] + ' input'+'\n')
        alldata['algo'][x[0]] = x[1]
        log.joint(x[0] + ' ' + str(x[1])+ '\n')

    return 0


def read_config(log, filename):
    '''Read settings from configuration file'''

    log.joint("Reading config file " + filename + ".\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    alldata = {}
    lpfile = 'NONE'
    solfile = None
    structfile = 'NONE'
    ReadNonzerosInSolution = 0
    loudconstraints = 0
    linenum = 0

    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'LPFILE':
                lpfile = thisline[1]
            elif word == 'SOLFILE':
                solfile = thisline[1]
                if len(thisline) > 2 and thisline[2] == 'NONZEROS':
                    ReadNonzerosInSolution = 1
            elif word == 'LOUDCONSTRAINTS':
                loudconstraints = 1
            elif word == 'STRUCTFILE':
                structfile = thisline[1]
            elif word == 'PARAMFILE':
                paramfile = thisline[1]
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + "\n")

        linenum += 1

    # removed ('SOLFILE', solfile), ('NONZEROSINSOL', ReadNonzerosInSolution)
    for x in [('LPFILE',lpfile), ('LOUDCONSTRAINTS', loudconstraints), ('STRUCTFILE', structfile), ('PARAMFILE', paramfile)]:
        if x[1] == 'NONE':
            log.stateandquit(' no ' + x[0] + ' input'+'\n')
        alldata[x[0]] = x[1]
        log.joint(x[0] + ' ' + str(x[1])+ '\n')

    return alldata


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit('usage: drsk0.py configfile')

    # Get config file
    configfile = 'drsk.conf'
    if len(sys.argv) == 2:
        configfile = sys.argv[1]

    # Create logger
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    logfile = "drsk_" + datetime_string + ".log"
    log = danoLogger(logfile)
    stateversion(log)

    # Read config file
    alldata = read_config(log, configfile)
    alldata['log'] = log

    # Read parameter file
    alldata['algo'] = {}
    retcode = drsk_readparameters(alldata, alldata['PARAMFILE'])

    # Read lp as gurobimodel
    drsk_getlp(alldata)

    # Optional: read solution (not fully set up yet)
    # retcode = drsk_readsolution(alldata, alldata['SOLFILE'])
    # if retcode:
    #     log.closelog()
    #     sys.exit('bye.')

    # Allocate memory for solution
    solutionvectordictionary = {}
    gurobimodel = alldata['gurobimodel']  
    for var in gurobimodel.getVars():
        solutionvectordictionary[var.varname] = 0
    alldata['solutionvectordictionary'] = solutionvectordictionary

    # Track iteration number
    alldata['algo']['iterations'] = {}
    alldata['algo']['iteration_cnt'] = 0

    # Record objective value of read solution
    #alldata['zeroobjval'] = objval = drsk_getobjectivevalue(alldata, alldata['solutionvectordictionary'], loud = 1)

    useimplicitstruct = alldata['STRUCTFILE'] == 'implicit'

    # Store all constraint data for LP
    drsk_storelp(alldata, getstruct=useimplicitstruct, loud=alldata.get('loud', 0))

    if useimplicitstruct:
        # Use implicit structure from LP
        structure = alldata['structure'] = {}
        structure.update(alldata['implicitstructure'])
    else:
        # Read structure of features from structure file
        retcode = drsk_readstructure(alldata, alldata['STRUCTFILE'])
        if retcode:
            log.closelog()
            sys.exit('bye.')

    # Run algo
    retcode, condition = drsk_greedy(alldata)  #softmax(alldata)
    if retcode:
        log.closelog()
        sys.exit('bye.')
        
    # Check solution
    log.joint('Skipping solution check\n')
    #retcode = drsk_checksolution(alldata)
    #log.joint('Solution checked with code %d.\n'%(retcode))
    
    log.closelog()    
