###############################################################################
# Functions for handling file reading and writing:
#   - reading configuration file
#   - reading parameter file
#   - reading instance file
#   - reading solution file
#   - writing all data
#   - writing cut modfile
#   - reading cut file
#   - writing cut file
#
# Blake Sisson mbs2246@columbia.edu
# 10/19/2026
###############################################################################
import sys
import json
from pathlib import Path
from myutils import breakexit


def drsk_read_config(log, filename):
    '''Read settings from configuration file'''
    log.joint("Reading configuration file " + filename + "...\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    config_data = {}
    paramfile = 'NONE'
    modfile = 'NONE'
    lpfile = 'NONE'
    solfile = 'NONE'
    cutfile_in = 'NONE'
    cutfile_out = 'NONE'
    instance_file = 'NONE'

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'PARAMFILE':
                paramfile = thisline[1]
            elif word == 'MODFILE':
                modfile = thisline[1]
            elif word == 'LPFILE':
                lpfile = thisline[1]
            elif word == 'SOLFILE':
                solfile = thisline[1]
            elif word == 'CUTFILE':
                type = thisline[1]
                if type == 'in':
                    cutfile_in = thisline[2]
                elif type == 'out':
                    cutfile_out = thisline[2]
            elif word == 'INSTANCE_FILE':
                instance_file = thisline[1]
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + " in config file " + filename + "\n")

        linenum += 1

    for x in [('PARAMFILE', paramfile),
              ('MODFILE', modfile),
              ('LPFILE', lpfile),
              ('SOLFILE', solfile),
              ('CUTFILE_in', cutfile_in),
              ('CUTFILE_out', cutfile_out),
              ('INSTANCE_FILE', instance_file)]:
        config_data[x[0]] = x[1]

    log.joint("Done reading configuration file " + filename + ".\n")
    return config_data


def drsk_read_paramfile(log, filename):
    '''Read parameters from file into local dictionary and return it'''
    log.joint("Reading parameter file " + filename + "...\n")
    params = {}

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    solver = 'None'
    theta = 'None'
    lam_hi = 'None'
    lam_lo = 'None'
    xi = 'None'
    budget = 'None'
    phi_scale = 'None'
    alpha = 'None'
    decimal_risk_thresh = 'None'
    ncuts_add = 'None'
    cut_phiThresh = 'None'
    cut_method = 'None'
    maxcuts = 'None'
    tol = 'None'
    maxits = 'None'
    PhiReduc = 'None'
    zerothresh = 'None'
    solve_time_limit = 'None'
    loud = 0
    verbose = 0
    breakpoints = 0

    linenum = 0
    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'solver':
                solver = thisline[1]
            elif word == 'theta':
                theta = thisline[1]
            elif word == 'lam_hi':
                lam_hi = float(thisline[1])
            elif word == 'lam_lo':
                lam_lo = float(thisline[1])
            elif word == 'xi':
                xi = float(thisline[1])
            elif word == 'budget':
                budget = float(thisline[1])
            elif word == 'phi_scale':
                phi_scale = thisline[1]
            elif word == 'alpha':
                alpha = float(thisline[1])
            elif word == 'decimal_risk_thresh':
                decimal_risk_thresh = int(thisline[1])
            elif word == 'ncuts_add':
                ncuts_add = int(thisline[1])
            elif word == 'cut_phiThresh':
                cut_phiThresh = float(thisline[1])
            elif word == 'cut_method':
                cut_method = thisline[1]
            elif word == 'maxcuts':
                maxcuts = int(thisline[1])
            elif word == 'tol':
                tol = float(thisline[1])
            elif word == 'maxits':
                maxits = int(thisline[1])
            elif word == 'PhiReduc':
                PhiReduc = float(thisline[1])
            elif word == 'zerothresh':
                zerothresh = float(thisline[1])
            elif word == 'solve_time_limit':
                solve_time_limit = int(thisline[1])
            elif word == 'loud':
                loud = int(thisline[1])
            elif word == 'verbose':
                verbose = int(thisline[1])
            elif word == 'breakpoints':
                breakpoints = int(thisline[1])
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input: " + word + " in parameter file" + filename + "\n")
                continue

        linenum += 1

    for x in [('solver', solver),
              ('theta', theta),
              ('lam_hi', lam_hi),
              ('lam_lo', lam_lo),
              ('xi', xi),
              ('budget', budget),
              ('phi_scale', phi_scale),
              ('alpha', alpha),
              ('decimal_risk_thresh', decimal_risk_thresh),
              ('ncuts_add', ncuts_add),
              ('cut_phiThresh', cut_phiThresh),
              ('cut_method', cut_method),
              ('maxcuts', maxcuts),
              ('tol', tol),
              ('maxits', maxits),
              ('PhiReduc', PhiReduc),
              ('zerothresh', zerothresh),
              ('solve_time_limit', solve_time_limit),
              ('loud', loud),
              ('verbose', verbose),
              ('breakpoints', breakpoints)]:
        if x[1] == 'NONE':
            log.stateandquit(' no ' + x[0] + ' input'+'\n')
        params[x[0]] = x[1]
        log.joint(x[0] + ' ' + str(x[1])+ '\n')

    log.joint("Done reading parameter file " + filename + ".\n")
    return params


def drsk_read_instancefile(log, instance_file):
    '''Read instances from file and return list of ids'''
    log.joint("Reading instance file " + instance_file + "...\n")
    try:
        f = open(instance_file, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + instance_file + "\n")

    instance_ids = []

    linenum = 0
    thisline = lines[linenum].split()
    name = thisline[1]
    linenum += 1

    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]
            if word == 'END':
                break
            instance_ids.append(word)
        linenum += 1

    log.joint("Done reading instance file " + instance_file + ".\n")
    return name, instance_ids


def drsk_read_solfile(log, filename):
    '''Read solutions from file and return dictionary mapping var names to value'''
    log.joint("Reading solution from file " + filename + "...\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    soln_dict = {}

    linenum = 0
    thisline = lines[linenum].split()
    if len(thisline) > 0 and thisline[0] == 'objvar':
        objval = float(thisline[1])
    linenum = 1  # skip first line which containing objective info

    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            if thisline[0] == 'END':
                break

            varname = thisline[0]
            varval = float(thisline[1])
            soln_dict[varname] = varval

        linenum += 1

    log.joint("Done reading solution from file " + filename + ".\n")
    return objval, soln_dict


def drsk_write_alldata(alldata, filename):
    '''Writing alldata to given file'''
    log = alldata['log']
    log.joint("Writing alldata to file " + filename + "...\n")

    def is_serializable(value):
        try:
            json.dumps(value)
            return True
        except TypeError:
            return False
    clean_data = {k: v for k, v in alldata.items() if is_serializable(v)}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            clean_data, 
            f, 
            indent=4,          # Adds 4 spaces of indentation
            sort_keys=True,     # Sorts the dictionary keys alphabetically
            ensure_ascii=False  # Keeps non-English/Unicode text intact
        )

    log.joint("Done writing alldata to file " + filename + ".\n")
    if alldata['breakpoints']: breakexit('Saved all data to file')


def drsk_write_cutmodfile(log, org_modfile, ampl):
    # Get path of new file
    directory_path = Path(org_modfile).parent
    base_name = Path(org_modfile).name
    new_path = str(directory_path) + "/cuts/cuts_" + str(base_name)

    # Ensure cuts directory exists
    Path(new_path).parent.mkdir(parents=True, exist_ok=True)

    log.joint("Writing cut model to modfile: " + new_path + "...\n")

    # Write ampl model to file
    ampl.export_model(new_path)

    log.joint('Done writing new model to modfile: %s.\n'%new_path)


def drsk_read_cutfile(alldata, filename):
    log = alldata['log']
    log.joint("Reading cut file: " + filename + "...\n")

    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file %s\n" %(filename))
        sys.exit(1)

    # Data structures to populate
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']
    nonzero_phiQuadweights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    # Retrieve max cuts
    maxcuts = alldata['cut_data']['maxcuts']

    # First line is how many cuts to read
    linenum = 0
    thisline = lines[linenum].split()
    readnumcuts = int(thisline[0])
    if maxcuts < 0:
        numcuts = readnumcuts                                                                     
    else:
        numcuts = min(maxcuts, readnumcuts)

    alldata['cut_data']['numcuts'] = numcuts
    log.joint('Using %d cuts.\n' %numcuts)
    if alldata['breakpoints']: breakexit('num cuts')

    Theta = alldata['prob_data']['Theta'] = float(thisline[3])
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))

    for cutnum in range(1, numcuts+1):
        linenum += 2   # first line is just cut count

        # Read cutweights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            weight = float(thisline[1])
            nonzero_cutweights.append((cutnum, featname))
            cutweights[(cutnum, featname)] = weight

        # Read phiQuadWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            var1idx = thisline[1]
            var2idx = thisline[2]
            weight = float(thisline[3])
            nonzero_phiQuadweights.append((cutnum, featname, var1idx, var2idx))
            phiQuadWeights[(cutnum, featname, var1idx, var2idx)] = weight

        # Read phiLinWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            varidx = thisline[1]
            weight = float(thisline[2])
            nonzero_phiLinWeights.append((cutnum, featname, varidx))
            phiLinWeights[(cutnum, featname, varidx)] = weight

        # Read phiConstWeights
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            weight = float(thisline[1])
            phiConstWeights[(cutnum, featname)] = weight

        # Read phiMinusToggle
        thisline = lines[linenum].split()
        count = int(thisline[2])
        for _ in range(1, count+1):
            linenum += 1
            thisline = lines[linenum].split()
            featname = thisline[0]
            toggle = int(thisline[1])
            phiMinusToggle[(cutnum, featname)] = toggle

        linenum += 1 #empty row

    log.joint("Done reading cut file: " + filename + ".\n")


def drsk_write_cutfile(alldata, filename):
    log = alldata['log']
    log.joint("Writing cut file: " + filename + "...\n")

    try:
        f = open(filename, "w")
    except:
        log.stateandquit("cannot write to file %s\n" %(filename))
        sys.exit(1)

    # Data structures to write
    nonzero_cutweights = alldata['cut_data']['nonzero_cutweights']
    cutweights = alldata['cut_data']['cutweights']
    nonzero_phiQuadWeights = alldata['cut_data']['nonzero_phiQuadWeights']
    phiQuadWeights = alldata['cut_data']['phiQuadWeights']
    nonzero_phiLinWeights = alldata['cut_data']['nonzero_phiLinWeights']
    phiLinWeights = alldata['cut_data']['phiLinWeights']
    phiConstWeights = alldata['cut_data']['phiConstWeights']
    phiMinusToggle = alldata['cut_data']['phiMinusToggle']

    numcuts = alldata['cut_data']['numcuts']
    log.joint('Writing %d cuts.\n' %numcuts)
    if alldata['breakpoints']: breakexit('num cuts')

    Theta = alldata['prob_data']['Theta']
    log.joint('numcuts: %d; Theta: %g\n' %(numcuts, Theta))
    f.write('%d Cuts Theta %g\n'%(numcuts, Theta))

    for cutnum in range(1, numcuts+1):
        f.write('Cut %d\n'%cutnum)

        # Write cutweights
        these_nonzero_cutweights = [tuple for tuple in nonzero_cutweights if tuple[0] == cutnum]
        count = len(these_nonzero_cutweights)
        f.write('  cutweights len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            weight = cutweights[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, weight))

        # Write phiQuadWeights
        these_nonzero_phiQuadWeights = [tuple for tuple in nonzero_phiQuadWeights if tuple[0] == cutnum]
        count = len(these_nonzero_phiQuadWeights)
        f.write('  phiQuadWeights len %d\n'%count)
        for tuple in these_nonzero_phiQuadWeights:
            featname = tuple[1]
            var1idx = tuple[2]
            var2idx = tuple[3]
            weight = phiQuadWeights[(cutnum, featname, var1idx, var2idx)]
            f.write('    %s %d %d %g\n'%(featname, var1idx, var2idx, weight))

        # Write phiLinWeights
        these_nonzero_phiLinWeights = [tuple for tuple in nonzero_phiLinWeights if tuple[0] == cutnum]
        count = len(these_nonzero_phiLinWeights)
        f.write('  phiLinWeights len %d\n'%count)
        for tuple in these_nonzero_phiLinWeights:
            featname = tuple[1]
            varidx = tuple[2]
            weight = phiLinWeights[(cutnum, featname, varidx)]
            f.write('    %s %d %g\n'%(featname, varidx, weight))

        # Read phiConstWeights
        count = len(these_nonzero_cutweights)
        f.write('  phiConstWeights len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            weight = phiConstWeights[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, weight))

        # Read phiMinusToggle
        count = len(these_nonzero_cutweights)
        f.write('  phiMinusToggle len %d\n'%count)
        for tuple in these_nonzero_cutweights:
            featname = tuple[1]
            toggle = phiMinusToggle[(cutnum, featname)]
            f.write('    %s %g\n'%(featname, toggle))

        f.write('\n')

    # Close writier
    f.close()
    log.joint("Done writing cut file: " + filename + ".\n")