import sys
from datetime import datetime
from log import danoLogger
from drsk_main import drsk_start, read_config


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
    lp_file = data['LPFILE']
    cut_file_in = data['CUTFILE_in']
    cut_file_out = data['CUTFILE_out']

    # Call drsk
    drsk_start(log, param_file, mod_file, lp_file, cut_file_in, cut_file_out)

    

    

