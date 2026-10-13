import sys
from datetime import datetime
from log import danoLogger
from drsk_main import drsk_start


def read_config(log, filename):
    '''Read settings from configuration file'''
    try:
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
    except:
        log.stateandquit("cannot open file " + filename + "\n")

    config_data = {}
    paramfile = 'NONE'
    modfile = 'NONE'
    cutfile = 'NONE'
    linenum = 0

    while linenum < len(lines):
        thisline = lines[linenum].split()
        if len(thisline) > 0 and thisline[0][0] != '#':
            word = thisline[0]

            if word == 'PARAMFILE':
                paramfile = thisline[1]
            elif word == 'MODFILE':
                modfile = thisline[1]
            elif word == 'CUTFILE':
                cutfile = thisline[1]
            elif word == 'END':
                break
            else:
                log.stateandquit("illegal input " + word + "\n")

        linenum += 1

    for x in [('PARAMFILE', paramfile),
              ('MODFILE',modfile),
              ('CUTFILE', cutfile)]:
        config_data[x[0]] = x[1]

    return config_data


if __name__ == "__main__":
    '''Get arguments and call drsk '''
    if len(sys.argv) < 2:
        sys.exit('usage: run.py configfile')

    # Get config file
    configfile = 'drsk.conf'
    if len(sys.argv) == 2:
        configfile = sys.argv[1]

    # Create logger
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_file = "drsk_" + datetime_string + ".log"
    log = danoLogger(log_file)

    # Read config file
    data = read_config(log, configfile)

    # Get files from arguments
    param_file = data['PARAMFILE']
    mod_file = data['MODFILE']
    cut_file = data.get('CUTEFILE', 'cutsrun.dat')

    drsk_start(log, param_file, mod_file, cut_file)

    

    

