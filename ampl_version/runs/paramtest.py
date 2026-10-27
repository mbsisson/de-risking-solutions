import sys
import os
import numpy as np
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
    reslog = danoLogger("paramtest_" + datetime_string + ".log")

    # Read config file
    data = drsk_read_config(log, configfile)

    # Get files from arguments
    param_file = data['PARAMFILE']
    mod_file = data['MODFILE']
    lp_file = data['LPFILE']
    sol_file = data['SOLFILE']
    cut_file_in = data['CUTFILE_in']
    cut_file_out = data['CUTFILE_out']

    param_dict = {}

    reslog.joint('Testing choices for xi\n----------------------\n\n')

    # Static
    reslog.joint('Parameters:\n')
    for x in [('solver', 'gurobi'),  #'/Applications/knitro-16.0.0-ARM-MacOS/bin/knitroampl'
              ('theta', 'auto'),
              ('lam_hi', 10.0),
              ('lam_lo', 9.0),
              ('budget', 0.01),
              ('phi_scale', 'percent_violation'),  #'scaled_abs_violation
              ('alpha', 10.0),
              ('decimal_risk_thresh', 3),
              ('ncuts_add', 1),
              ('cut_phiThresh', 0.25),
              ('cut_method', 'greedy'),  #'quasi-greedy'
              ('maxcuts', 100),
              ('tol', 1e-4),
              ('maxits', 10),
              ('PhiReduc', 0.1),
              ('zerothresh', 1e-8),
              ('solve_time_limit', 45),
              ('loud', 1),
              ('verbose', 0),
              ('breakpoints', 0)]:
        param_dict[x[0]] = x[1]
        reslog.joint('  ' + x[0] + ' ' + str(x[1])+ '\n')
    reslog.joint('\n')

    for xi in np.arange(2.5, 50.0, 2.5):
        reslog.joint('TESTING xi = %g\n'%xi)
        param_dict['xi'] = xi

        result_str = ''

        try:
            result_str = drsk_start(log, param_file, mod_file, lp_file, sol_file, cut_file_in, cut_file_out, param_dict)
        except Exception as e:
            result_str = f"An error occured: {e}\n"

        reslog.joint(result_str)
        reslog.joint("==========================================================================\n\n")

    reslog.joint("ALL DONE\n")

    

    

