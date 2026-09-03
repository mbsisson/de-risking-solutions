import argparse
import numpy as np
import gurobipy as gp
from gurobipy import GRB

# Problem: VarNum is not defined in Gurobi

def get_objective_value(gurobimodel, vector):
    '''
    Evaluate objective at a given vector
    '''
    obj = gurobimodel.getObjective()

    if isinstance(obj, gp.QuadExpr):
        objisquad = True
        lin_obj = obj.getLinExpr()
        q_obj = obj - lin_obj
    else:      
        objisquad = False
        lin_obj = obj

    quadterm = 0
    if objisquad:
        for j in range(q_obj.size()):
            v1index = q_obj.getVar1(j).index
            v2index = q_obj.getVar2(j).index
            coeff = q_obj.getCoeff(j)
            thisterm = coeff*vector[v1index]*vector[v2index]
            quadterm += thisterm

    linterm = 0
    linterm_noPhi = 0
    for j in range(lin_obj.size()):
        varindex = lin_obj.getVar(j).index
        coeff = lin_obj.getCoeff(j)
        linterm += coeff*vector[varindex]

    constant = lin_obj.getConstant()
    total = quadterm + linterm + constant

    return total


def get_objective_gradient(model):
    """
    Compute gradient of quadratic objective at current solution.

    For:
        f(x) = x'Qx + c'x + constant

    Gurobi stores quadratic terms as:
        q*x_i*x_j

    Note:
        Gurobi's quadratic objective convention is:
        sum q_ij x_i x_j
    """

    vars = model.getVars()
    n = len(vars)

    grad = np.zeros(n)

    obj = model.getObjective()

    # If the objective is Quadratic
    if isinstance(obj, gp.QuadExpr):
        print("Objective is quadratic")
        # Handle quad terms
        for term_idx in range(obj.size()):
            xi = obj.getVar1(term_idx)
            i = xi.index
            val_xi = xi.X

            xj = obj.getVar2(term_idx)
            j = xj.index
            val_xj = xj.X

            coeff = obj.getCoeff(term_idx)

            if i == j:
                # coeff*x_i^2
                grad[i] += 2 * coeff * val_xi
            else:
                # coeff*x_i*x_j
                grad[i] += coeff * val_xj
                grad[j] += coeff * val_xi

            #print(f"Quadratic term: {coeff} * {xi.VarName} * {xj.VarName}")
        
        # Extract the linear portion embedded inside the QuadExpr
        lin_expr = obj.getLinExpr()

    else:
        print("Objective is linear")
        lin_expr = obj

    # Handle linear terms
    for term_idx in range(lin_expr.size()):
        coeff = obj.getCoeff(term_idx)
        i = lin_expr.getVar(term_idx).index
        grad[i] = coeff

        #print(f"Linear term: {coeff} * {lin_expr.getVar(term_idx).VarName}")

    print(grad)
    return grad


def evaluate_constraints(model, x):
    """
    Compute the slack of every linear and quadratic constraint in a Gurobi model
    evaluated at a given vector x.

    Parameters
    ----------
    model : gp.Model
        Gurobi model.
    x : numpy array
        Value of every variable, in the same order as model.getVars().

    Returns
    -------
    dict
        Dictionary mapping constraint names to slacks.
    """
    vars = model.getVars()
    if len(x) != len(vars):
        raise ValueError("Length of x must equal number of variables.")

    # Map variable -> value
    #val = {v: float(x[i]) for i, v in enumerate(vars)}

    slacks = {}

    # Linear constraints
    for constr in model.getConstrs():

        row = model.getRow(constr)
        lhs = 0.0
        for term_idx in range(row.size()):
            coeff = row.getCoeff(term_idx)
            i = row.getVar(term_idx).index
            lhs += coeff * x[i]

        rhs = constr.RHS

        if constr.Sense == GRB.LESS_EQUAL:
            slack = rhs - lhs
        elif constr.Sense == GRB.GREATER_EQUAL:
            slack = lhs - rhs
        elif constr.Sense == GRB.EQUAL:
            slack = abs(lhs - rhs)
        else:
            raise RuntimeError(f"Unknown constraint sense {constr.Sense}")
            
        slacks[constr.ConstrName] = slack

    # Quadratic constraints
    for qc in model.getQConstrs():

        qrow = model.getQCRow(qc)

        lhs = 0.0

        # Linear part
        linQc  = qrow.getLinExpr()
        for term_idx in range(linQc.size()):
            coeff = linQc.getCoeff(term_idx)
            xi = x[linQc.getVar(term_idx).index]
            lhs += coeff * xi

        # Quadratic part
        quadQc = qrow - linQc
        for term_idx in range(quadQc.size()):
            i = quadQc.getVar1(term_idx).index
            j = quadQc.getVar2(term_idx).index
            coeff = qrow.getCoeff(i)
            lhs += coeff * x[i] * x[j]

        rhs = qc.QCRHS

        if qc.QCSense == GRB.LESS_EQUAL:
            slack = rhs - lhs
        elif qc.QCSense == GRB.GREATER_EQUAL:
            slack = lhs - rhs
        elif qc.QCSense == GRB.EQUAL:
            slack = abs(lhs - rhs)
        else:
            raise RuntimeError(f"Unknown constraint sense {qc.QCSense}")

        slacks[qc.QCName] = slack

    return slacks


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "lpfile",
        help="QCQP LP file"
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="Perturbation magnitude"
    )

    parser.add_argument(
        "--relative",
        action="store_true",
        help="Scale alpha relative to ||x||"
    )

    args = parser.parse_args()


    # ---------------------------
    # Load and solve
    # ---------------------------

    model = gp.read(args.lpfile)

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(
            "Model was not solved optimally"
        )

    vars = model.getVars()

    xstar = np.array(
        [v.X for v in vars]
    )

    objstar = model.ObjVal

    print("Optimal objective:")
    print(objstar)


    # ---------------------------
    # Compute gradient
    # ---------------------------

    grad = get_objective_gradient(model)

    norm = np.linalg.norm(grad)

    if norm < 1e-12:
        raise RuntimeError(
            "Objective gradient is zero"
        )


    direction = -grad / norm


    # ---------------------------
    # Perturb
    # ---------------------------

    alpha = args.alpha

    if args.relative:
        alpha *= np.linalg.norm(xstar)


    xnew = xstar + alpha * direction


    # ---------------------------
    # Evaluate objective
    # ---------------------------

    objnew = get_objective_value(model, xnew)

    print("\nPerturbed objective:")
    print(objnew)

    print("\nObjective change:")
    print(objnew - objstar)


    # ---------------------------
    # Check violations
    # ---------------------------

    slacks = evaluate_constraints(model, xstar)

    print("\nSlacks of optimal:")

    if len(slacks) == 0:
        print("None")
    else:
        for name, value in slacks.items():
            print(f"{name}: {value}")

    slacks = evaluate_constraints(model, xnew)

    print("\nSlacks of perturbed optimal:")

    if len(slacks) == 0:
        print("None")
    else:
        for name, value in slacks.items():
            print(f"{name}: {value}")


    # ---------------------------
    # Save solution
    # ---------------------------

    with open("perturbed.sol", "w") as f:

        for v, val in zip(vars, xnew):
            if abs(val) > 1e-10:
                f.write(
                    f"{v.VarName} = {val}\n"
                )

        f.write("END\n")


    print("\nSaved perturbed.sol")


if __name__ == "__main__":
    main()