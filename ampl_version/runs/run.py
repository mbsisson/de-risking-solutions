import sys
import os
from datetime import datetime
from log import danoLogger

# Get the absolute path to src directory and insert into sys.path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, module_path)

from drsk_main import drsk_start, drsk_read_config


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
    log = danoLogger("drsk_" + datetime_string + ".log")

    # Read config file
    data = drsk_read_config(log, configfile)

    # Get files from arguments
    param_file = data['PARAMFILE']
    mod_file = data['MODFILE']
    lp_file = data['LPFILE']
    sol_file = data['SOLFILE']
    sol_file_out = "sols/drsk_" + datetime_string + ".sol"
    cut_file_in = data['CUTFILE_in']
    cut_file_out = data['CUTFILE_out']
    ref_sol_file = data['REFSOLFILE']

    # Call drsk
    drsk_start(log,
               param_file,
               mod_file,
               lp_file,
               sol_file,
               sol_file_out,
               cut_file_in,
               cut_file_out,
               ref_sol_file)

    

    

