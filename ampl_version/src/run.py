import sys
from datetime import datetime
from drsk_main import drsk


if __name__ == "__main__":
    '''Get arguments and call drsk '''
    if len(sys.argv) < 2:
        sys.exit('usage: ampl_test.py [modfile]')

    # Get files from arguments
    mod_file = sys.argv[1]
    cut_file = 'cutsrun.dat' if len(sys.argv) == 2 else sys.argv[2]

    # Create logger
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_file = "drsk_" + datetime_string + ".log"

    drsk(log_file, mod_file, cut_file)

    

    

