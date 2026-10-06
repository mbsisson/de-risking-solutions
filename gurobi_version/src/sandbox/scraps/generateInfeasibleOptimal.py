import argparse
import gurobipy as gp
from gurobipy import GRB
from myutils import breakexit

# Runs poorly for large QCQPs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lpfile")
    parser.add_argument("--delta", type=float, default=0.01,
                        help="Required objective improvement.")
    args = parser.parse_args()

    # -----------------------
    # Load model
    # -----------------------
    model = gp.read(args.lpfile)

    # Solve original model
    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError("Original model was not solved to optimality.")

    objstar = model.ObjVal
    sense = model.ModelSense

    print(f"Optimal objective = {objstar}")

    breakexit("Solved problem")

    # -----------------------
    # Add objective cutoff (relative to optimal objective value)
    # -----------------------
    obj = model.getObjective()

    if sense == GRB.MINIMIZE:
        cutoff = objstar * (1 - args.delta) if objstar >= 0 else objstar * (1 + args.delta)
        model.addConstr(obj <= cutoff, name="objective_cutoff")
    else:
        cutoff = objstar * (1 + args.delta) if objstar >= 0 else objstar * (1 - args.delta)
        model.addConstr(obj >= cutoff, name="objective_cutoff")
        
    breakexit("Added objective cutoff")

    # -----------------------
    # Build feasibility relaxation
    # -----------------------
    model.feasRelaxS(
        relaxobjtype=0,   # sum of violations
        minrelax=True,    # optimize relaxation amount
        vrelax=True,      # relax variable bounds
        crelax=True       # relax constraints
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:

        print("\nRecovered minimally infeasible solution")
        print(f"Objective = {model.ObjVal}")

        print("\nVariable values")
        for v in model.getVars():
            if abs(v.X) > 1e-9:
                print(f"{v.VarName:20s} {v.X:15.8f}")

    else:
        print("No solution satisfying the requested objective improvement.")


if __name__ == "__main__":
    main()