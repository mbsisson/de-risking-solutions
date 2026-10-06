import sys
import gurobipy as gp

if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit('usage: getLPfile.py somefileformat')

    alldata = {}
    somefileformat = sys.argv[1]
    gurobimodel = gp.read(somefileformat)

    filename = somefileformat
    filename = filename.split('/')[-1]
    filename = filename.split('.')[0]
    filename += ".lp"

    gurobimodel.write(filename)
