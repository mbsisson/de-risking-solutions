import sys
import os
import pulp

def convert(lp_path):
    '''Converts LP file into mod and dat file for AMPL'''

    # Load the .lp file
    problem = pulp.LpProblem.from_file(lp_path)

    # splitext splits the path into ('document', '.lp')
    base_name, _ = os.path.splitext(lp_path)
    # Combine the base name with the new extension
    mod_file_name = base_name + ".mod"
    dat_file_name = base_name + ".dat"

    # Write .mod file (Model structure)
    with open(mod_file_name, "w") as mod:
        mod.write("# Generated AMPL Model from LP file\n\n")
    for var in problem.variables():
        low = var.lowBound if var.lowBound is not None else "-Infinity"
        up = var.upBound if var.upBound is not None else "Infinity"
        mod.write(f"var {var.name} >= {low}, <= {up};\n")

    if problem.sense == pulp.LpMaximize:
        mod.write("\nmaximize obj: ")
    else:
        mod.write("\nminimize obj: ")

    obj_expr = " + ".join(
        f"{coef} * {var.name}" for var, coef in problem.objective.items()
    )
    mod.write(obj_expr + ";\n\n")

    for name, constraint in problem.constraints.items():
        expr = " + ".join(
        f"{coef} * {var.name}" for var, coef in constraint.items()
        )
        if constraint.sense == 1:  # >=
            rel = ">="
        elif constraint.sense == -1:  # <=
            rel = "<="
        else:
            rel = "="
        mod.write(f"subject to {name}: {expr} {rel} {constraint.constant};\n")

    # Write .dat file (Variable bounds / Data if needed)
    with open(dat_file_name, "w") as dat:
        dat.write("# Data file placeholder\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: converter.py LP_file_path')

    lpfile = sys.argv[1]

    convert(lpfile)
