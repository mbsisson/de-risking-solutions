import sys
import re
import time
from pathlib import Path
from datetime import datetime
#from concurrent.futures import ThreadPoolExecutor, TimeoutError
import pyqplib
from log import danoLogger
from drsk_main import read_config, drsk_initialize


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
    cut_file_in = data['CUTFILE_in']
    cut_file_out = data['CUTFILE_out']

    # Set the directory path
    modfile_path = Path('../data')

    mod_file = "../data/mod/QPLIB_5543.mod"
    qplib_file = "../data/qplib/QPLIB_5543.qplib"
    
    problem = pyqplib.read_problem(qplib_file)
    print(problem)
    
    ################# Testing just one #########################
    #drsk_initialize(log, param_file, mod_file, cut_file_in, cut_file_out)




    ############### The loop over all qplib files #######################
    # # Get list of all mod files
    # modfiles = list(modfile_path.glob('QPLIB_*.mod'))

    # # Set maximum wait time
    # TIMEOUT_SECONDS = 10
    # for mod_file_path in modfiles:
    #     mod_file = str(mod_file_path)
        
    #     # Get instance id
    #     match = re.search(r"QPLIB_\s*(\d+)", mod_file)
    #     id = int(match.group(1))
    #     print("Looking at instance:", id)

    #     with ThreadPoolExecutor(max_workers=1) as executor:
    #         # Submit the function to the pool
    #         future = executor.submit(drsk_initialize, log, param_file, mod_file, cut_file_in, cut_file_out)
            
    #         try:
    #             # Wait for the result with a timeout
    #             alldata = future.result(timeout=TIMEOUT_SECONDS)
    #         except TimeoutError:
    #             print(f"Reading instance {id} timed out after {TIMEOUT_SECONDS} seconds. Breaking away.")
    #             continue

    #     print(" > Instance %d has %d features"%(id, alldata['struct_data']["numfeats"]))

            
