import sys
import os
from datetime import datetime
import gurobipy as gp
from log import danoLogger

# Get the absolute path to src directory and insert into sys.path
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, module_path)

from drsk_main import drsk_start, drsk_read_config, drsk_read_instancefile


if __name__ == "__main__":
    '''Get arguments and call drsk '''
    if len(sys.argv) < 2:
        sys.exit('usage: run.py configfile')

    # Get config file
    configfile = 'drsk.conf'
    if len(sys.argv) == 2:
        configfile = sys.argv[1]

    # Create loggers
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log = danoLogger("drsk_" + datetime_string + ".log")
    reslog = danoLogger("qplib_" + datetime_string + ".log")

    # Read config file
    data = drsk_read_config(reslog, configfile)

    # Get files from arguments
    param_file = data['PARAMFILE']
    cut_file_in = data['CUTFILE_in']
    cut_file_out = data['CUTFILE_out']
    instance_file = data['INSTANCE_FILE']

    # Get list of all files
    name, instance_ids = drsk_read_instancefile(reslog, instance_file)

    # Set the directory path
    modfile_dir = '../data/mod/'
    lpfile_dir = '../data/lp/'
    solfile_dir = '../data/sol/'

    for id in instance_ids:
        reslog.joint("Running on instance %s...\n"%id)

        mod_file = modfile_dir + name + '_' + id + '.mod'
        lp_file = lpfile_dir + name + '_' + id + '.lp'
        sol_file = solfile_dir + name + '_' + id + '.sol'

        result_str = ''

        if gp.read(lp_file).IsMIP:  # Check if model is a MIP
            result_str = "This instance is a MIP... skip it!\n"

        else:
            try:
                result_str = drsk_start(log, param_file, mod_file, lp_file, sol_file, cut_file_in, cut_file_out)
            except Exception as e:
                result_str = f"An error occured: {e}\n"

        reslog.joint(result_str)
        reslog.joint("==========================================================================\n\n")

    reslog.joint("ALL DONE\n")

    

    



    ############### For determining which instances are risky #######################
    # # Get list of all files
    # modfiles = list(modfile_path.glob('QPLIB_*.mod'))

    # risky_instance_count = 0
    # risky_instance_strlist = ""
    # unrisky_instance_count = 0
    # unrisky_instance_strlist = ""
    # for mod_file_path in modfiles:
    #     mod_file = str(mod_file_path)

    #     # Get instance id
    #     match = re.search(r"QPLIB_\s*(\d+)", mod_file)
    #     id = match.group(1)

    #     lp_file = "../data/lp/QPLIB_" + id + ".lp"

    #     alldata = drsk_initialize(log, param_file, mod_file, lp_file, cut_file_in, cut_file_out)

    #     # Read problem into AMPL
    #     drsk_read(alldata)

    #     # Store problem data and risk structure
    #     drsk_storelp(alldata)

    #     numfeats = alldata['struct_data']["numfeats"]
    #     if numfeats == 0:
    #         unrisky_instance_count += 1
    #         unrisky_instance_strlist += "%s\n"%id
    #     else:
    #         risky_instance_count += 1
    #         risky_instance_strlist += "%s %d\n"%(id, numfeats)

    # # Write risky instances to file
    # with open("risky_instances.txt", "w", encoding="utf-8") as file:
    #     output = str(risky_instance_count) + "\n" + risky_instance_strlist + "END\n"
    #     file.write(output)

    # # Write unrisky instances to file
    # with open("unrisky_instances.txt", "w", encoding="utf-8") as file:
    #     output = str(unrisky_instance_count) + "\n" + unrisky_instance_strlist + "END\n"
    #     file.write(output)

            
