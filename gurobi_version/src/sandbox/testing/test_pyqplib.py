import sys
import numpy as np
import pyqplib


def extract_qplib_data(prob, zero_tol=0.0):
    """
    Extract objective and constraint data from a PyQPLIB Problem object.

    Each constraint contains:
        sense       : '=', '<=', '>=', or 'range'
        rhs         : scalar RHS when representable by one bound;
                      otherwise None
        lb, ub      : original lower and upper bounds
        linear      : {variable_name: coefficient}
        quadratic   : {(variable_name_1, variable_name_2): coefficient}
        degree      : 0, 1, or 2
        constant    : constant term
        inf_norm    : infinity norm of all nonconstant coefficients

    Quadratic terms are stored as coefficients of monomials:
        coefficient * x_i * x_j

    Returns:
        {
            "name": ...,
            "num_vars": ...,
            "variables": ...,
            "objective": ...,
            "constraints": [...]
        }

    Notes:
      - `zero_tol=0.0` preserves every coefficient except exact zeros.
      - Quadratic coefficient convention is determined by the conversion
        of PyQPLIB's stored lower-triangle Hessian matrices below.
    """

    n = int(prob.num_vars)
    m = int(prob.num_cons)

    variable_names = [f"x{i + 1}" for i in range(n)]

    # --------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------

    # Convert an object exposing .row/.col/.data, a SciPy sparse matrix,
    # or a dense array to a dense numeric matrix.
    # def to_dense_matrix(M):
    #     print("M", type(M))

    #     if hasattr(M, "toarray"):
    #         return np.asarray(M.toarray(), dtype=float)

    #     if all(hasattr(M, attr) for attr in ("row", "col", "data", "shape")):
    #         result = np.zeros(M.shape, dtype=float)
    #         np.add.at(result, (M.row, M.col), M.data)
    #         return result

    #     return np.asarray(M, dtype=float)

    def clean_number(value):
        value = float(value)
        return 0.0 if abs(value) <= zero_tol else value

    def extract_linear(coefficients):
        coefficients = np.asarray(coefficients, dtype=float).reshape(-1)
        return {
            variable_names[i]: clean_number(value)
            for i, value in enumerate(coefficients)
            if abs(value) > zero_tol
        }

    def extract_quadratic(H):
        """
        Interpret a stored lower-triangle Hessian H as the Hessian
        of a quadratic function:
            f(x) = constant + c^T x + 0.5*x^T H*x.

        The monomial coefficients are:
            diagonal:     0.5 * H[i,i]
            off-diagonal: H[i,j], i != j

        This convention must be checked against the installed PyQPLIB
        implementation/version before relying on numerical coefficients.
        """
        quadratic = {}

        # Diagonal entries: coefficient of x_i^2 is H[i,i] / 2
        for i, value in zip(H.diag_rows, H.diag_vals):
            coefficient = clean_number(0.5 * value)
            if coefficient != 0.0:
                quadratic[(variable_names[int(i)], variable_names[int(i)])] = coefficient

        # Off-diagonal entries: coefficient of x_i*x_j is H[i,j]
        for i, j, value in zip(
            H.subdiag_rows, H.subdiag_cols, H.subdiag_vals
        ):
            coefficient = clean_number(value)
            if coefficient != 0.0:
                quadratic[(variable_names[int(j)], variable_names[int(i)])] = coefficient

        return quadratic

    def degree_of(linear, quadratic, constant):
        if quadratic:
            return 2
        if linear:
            return 1
        return 0

    def coefficient_inf_norm(linear, quadratic):
        values = (
            list(linear.values()) + list(quadratic.values())
        )
        return max((abs(v) for v in values), default=0.0)

    def bound_sense(lb, ub):
        lb_finite = np.isfinite(lb)
        ub_finite = np.isfinite(ub)

        if lb_finite and ub_finite and lb == ub:
            return "=", float(lb)
        if lb_finite and not ub_finite:
            return ">=", float(lb)
        if not lb_finite and ub_finite:
            return "<=", float(ub)
        if lb_finite and ub_finite:
            return "range", None

        return "free", None

    # --------------------------------------------------------
    # Objective
    # --------------------------------------------------------

    obj = prob.obj

    objective_linear = extract_linear(obj.lin)
    objective_quadratic = extract_quadratic(obj.hess(prob.x0))
    objective_constant = float(obj.offset)

    objective = {
        "sense": str(obj.sense),
        "linear": objective_linear,
        "quadratic": objective_quadratic,
        "degree": degree_of(
            objective_linear, objective_quadratic, objective_constant
        ),
        "constant": objective_constant,
        "inf_norm": coefficient_inf_norm(
            objective_linear, objective_quadratic
        ),
    }

    # --------------------------------------------------------
    # Constraints
    # --------------------------------------------------------

    cons = prob.constraints

    # Sparse matrix with shape (number of constraints, number of variables)
    A = cons.mat.tocsr() if hasattr(cons.mat, "tocsr") else cons.mat

    constraints = []

    for k in range(m):
        # Linear terms in constraint k
        row = A.getrow(k) if hasattr(A, "getrow") else np.asarray(A)[k]
        if hasattr(row, "indices") and hasattr(row, "data"):
            linear = {
                variable_names[int(i)]: clean_number(value)
                for i, value in zip(row.indices, row.data)
                if abs(value) > zero_tol
            }
        else:
            linear = extract_linear(row)

        # Quadratic terms
        H = cons.hess_mats[k]
        quadratic = extract_quadratic(H)

        lb = float(prob.cons_lb[k])
        ub = float(prob.cons_ub[k])
        sense, rhs = bound_sense(lb, ub)

        # PyQPLIB's constraints are represented by:
        #     lb <= quadratic + linear + constant <= ub
        #
        # In this representation, the stored constraint constant is
        # inferred from evaluation at zero, when supported by the API.
        zero = np.zeros(n, dtype=float)
        values_at_zero = np.asarray(prob.cons_val(zero), dtype=float)
        constant = float(values_at_zero[k])

        constraints.append({
            "name": f"c{k + 1}",
            "sense": sense,
            "rhs": rhs,
            "lb": lb,
            "ub": ub,
            "linear": linear,
            "quadratic": quadratic,
            "degree": degree_of(linear, quadratic, constant),
            "constant": constant,
            "inf_norm": coefficient_inf_norm(linear, quadratic),
        })

    # --------------------------------------------------------
    # Variables and output
    # --------------------------------------------------------

    variables = {
        variable_names[i]: {
            "lb": float(prob.var_lb[i]),
            "ub": float(prob.var_ub[i]),
            "initial": float(prob.x0[i]),
            "type": str(prob.var_types[i]),
        }
        for i in range(n)
    }

    return {
        "name": prob.name,
        "num_vars": n,
        "num_cons": m,
        "variables": variables,
        "objective": objective,
        "constraints": constraints,
    }


def hessian_inspection(prob):
    print("=" * 70)
    print("HESSIAN MATRIX STORAGE")
    print("=" * 70)

    # ------------------------------------------------------------
    # Objective Hessian
    # ------------------------------------------------------------

    H_obj = prob.obj.hess(prob.x0)

    print("\nObjective Hessian")
    print("type:", type(H_obj))
    print("shape:", H_obj.shape)
    print("nnz:", H_obj.nnz)

    if H_obj.nnz:
        print("data:", H_obj.data)
        print("row:", H_obj.row)
        print("col:", H_obj.col)


    # ------------------------------------------------------------
    # Constraint Hessians
    # ------------------------------------------------------------

    print("\nNumber of constraint Hessians:")
    print(len(prob.constraints.hess_mats))

    # Show the first few nonzero constraint Hessians
    shown = 0

    for k, H in enumerate(prob.constraints.hess_mats):

        print("H")
        print("type:", type(H))
        print("shape:", H.shape)
        print("nnz:", H.nnz)

        if H.nnz == 0:
            continue

        print("\n" + "-" * 60)
        print(f"Constraint {k + 1}")
        print("type:", type(H))
        print("shape:", H.shape)
        print("nnz:", H.nnz)

        print("data:", H.data)
        print("row:", H.row)
        print("col:", H.col)

        # Also show dense form for the first one or two
        print("\ndense:")
        print(H.toarray())

        shown += 1

        if shown >= 3:
            break


    # ------------------------------------------------------------
    # Constraint linear matrix
    # ------------------------------------------------------------

    A = prob.constraints.mat

    print("\n" + "=" * 70)
    print("LINEAR CONSTRAINT MATRIX")
    print("=" * 70)

    print("type:", type(A))
    print("shape:", A.shape)
    print("nnz:", A.nnz)

    print("\nFirst 20 nonzeros:")

    coo = A.tocoo()

    for r, c, v in zip(coo.row[:20], coo.col[:20], coo.data[:20]):
        print(f"constraint={r + 1}, variable={c + 1}, coefficient={v}")


    # ------------------------------------------------------------
    # Objective
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("OBJECTIVE DATA")
    print("=" * 70)

    print("sense:", prob.obj.sense)
    print("offset:", prob.obj.offset)
    print("linear:", prob.obj.lin)


    # ------------------------------------------------------------
    # Bounds
    # ------------------------------------------------------------

    print("\n" + "=" * 70)
    print("CONSTRAINT BOUNDS")
    print("=" * 70)

    print("First 20 constraint bounds:")

    for k in range(min(20, prob.num_cons)):
        print(
            f"constraint={k + 1}: "
            f"lb={prob.cons_lb[k]}, "
            f"ub={prob.cons_ub[k]}"
        )

def examine(qplib_file):
    # ============================================================
    # 1. Read a QPLIB problem
    # ============================================================

    prob = pyqplib.read_problem(qplib_file)

    print("\n" + "=" * 70)
    print("PROBLEM OBJECT")
    print("=" * 70)

    print("type(prob):")
    print(type(prob))

    print("\nAttributes / methods:")
    print([x for x in dir(prob) if not x.startswith("_")])


    # ============================================================
    # 2. Inspect the top-level Problem attributes
    # ============================================================

    print("\n" + "=" * 70)
    print("TOP-LEVEL ATTRIBUTES")
    print("=" * 70)

    for name in [
        "description",
        "obj",
        "constraints",
        "x0",
        "var_lb",
        "var_ub",
        "var_types",
    ]:
        print(f"\n{name}:")
        try:
            value = getattr(prob, name)
            print("  type:", type(value))
            print("  value:", value)
        except Exception as e:
            print("  ERROR:", repr(e))


    # ============================================================
    # 3. Inspect ProblemDescription
    # ============================================================

    print("\n" + "=" * 70)
    print("DESCRIPTION")
    print("=" * 70)

    try:
        desc = prob.description

        print("type:", type(desc))

        print("\nAttributes:")
        print([x for x in dir(desc) if not x.startswith("_")])

        print("\nAttribute values:")
        for name in dir(desc):
            if not name.startswith("_"):
                try:
                    value = getattr(desc, name)
                    if not callable(value):
                        print(f"  {name} = {value!r}")
                except Exception as e:
                    print(f"  {name} = <ERROR: {e}>")

    except Exception as e:
        print("ERROR:", repr(e))


    # ============================================================
    # 4. Inspect Objective
    # ============================================================

    print("\n" + "=" * 70)
    print("OBJECTIVE")
    print("=" * 70)

    try:
        obj = prob.obj

        print("type:", type(obj))

        print("\nAttributes / methods:")
        print([x for x in dir(obj) if not x.startswith("_")])

        print("\nNon-callable attributes:")
        for name in dir(obj):
            if not name.startswith("_"):
                try:
                    value = getattr(obj, name)
                    if not callable(value):
                        print(f"  {name} = {value!r}")
                except Exception as e:
                    print(f"  {name} = <ERROR: {e}>")

    except Exception as e:
        print("ERROR:", repr(e))


    # ============================================================
    # 5. Inspect Constraints
    # ============================================================

    print("\n" + "=" * 70)
    print("CONSTRAINTS")
    print("=" * 70)

    try:
        cons = prob.constraints

        print("type:", type(cons))

        print("\nAttributes / methods:")
        print([x for x in dir(cons) if not x.startswith("_")])

        print("\nNon-callable attributes:")
        for name in dir(cons):
            if not name.startswith("_"):
                try:
                    value = getattr(cons, name)
                    if not callable(value):
                        print(f"  {name} = {value!r}")
                except Exception as e:
                    print(f"  {name} = <ERROR: {e}>")

    except Exception as e:
        print("ERROR:", repr(e))


    # ============================================================
    # 6. Inspect signatures of important callable methods
    # ============================================================

    print("\n" + "=" * 70)
    print("METHOD SIGNATURES")
    print("=" * 70)

    import inspect


    def print_signature(obj, name):
        try:
            method = getattr(obj, name)
            print(f"\n{name}:")
            print("  signature:", inspect.signature(method))
            print("  docstring:")
            print(inspect.getdoc(method))
        except Exception as e:
            print(f"\n{name}: ERROR: {repr(e)}")


    print("\n--- Problem methods ---")

    for name in [
        "obj_val",
        "obj_grad",
        "cons_val",
        "cons_jac",
        "hess",
        "jac",
    ]:
        if hasattr(prob, name):
            print_signature(prob, name)


    print("\n--- Objective methods ---")

    if hasattr(prob, "obj"):
        for name in [
            "val",
            "grad",
            "hess",
        ]:
            if hasattr(prob.obj, name):
                print_signature(prob.obj, name)


    print("\n--- Constraint methods ---")

    if hasattr(prob, "constraints"):
        for name in [
            "val",
            "jac",
            "hess",
        ]:
            if hasattr(prob.constraints, name):
                print_signature(prob.constraints, name)


    # ============================================================
    # 7. Basic numerical information
    # ============================================================

    print("\n" + "=" * 70)
    print("NUMERICAL INFORMATION")
    print("=" * 70)

    try:
        x0 = np.asarray(prob.x0, dtype=float)

        print("\nx0:")
        print(x0)
        print("shape:", x0.shape)

        print("\nVariable lower bounds:")
        print(np.asarray(prob.var_lb))

        print("\nVariable upper bounds:")
        print(np.asarray(prob.var_ub))

        print("\nVariable types:")
        print(prob.var_types)

    except Exception as e:
        print("ERROR:", repr(e))


    # ============================================================
    # 8. Evaluate objective / constraints at x0
    # ============================================================

    print("\n" + "=" * 70)
    print("EVALUATION AT x0")
    print("=" * 70)

    try:
        x = np.asarray(prob.x0, dtype=float)

        if hasattr(prob, "obj_val"):
            print("\nObjective value:")
            print(prob.obj_val(x))

        if hasattr(prob, "obj_grad"):
            print("\nObjective gradient:")
            print(prob.obj_grad(x))

        if hasattr(prob, "cons_val"):
            print("\nConstraint values:")
            print(prob.cons_val(x))

        if hasattr(prob, "cons_jac"):
            print("\nConstraint Jacobian:")
            J = prob.cons_jac(x)
            print(J)
            print("shape:", np.asarray(J).shape)

    except Exception as e:
        print("ERROR:", repr(e))


    # ============================================================
    # 9. Test Hessian interfaces
    # ============================================================

    print("\n" + "=" * 70)
    print("HESSIAN TESTS")
    print("=" * 70)

    try:
        x = np.asarray(prob.x0, dtype=float)

        if hasattr(prob.obj, "hess"):
            print("\nObjective Hessian:")
            H = prob.obj.hess(x)
            print(H)
            print("shape:", np.asarray(H).shape)

    except Exception as e:
        print("\nObjective Hessian ERROR:")
        print(repr(e))


    try:
        x = np.asarray(prob.x0, dtype=float)

        if hasattr(prob, "hess"):
            print("\nProblem Hessian method exists.")

            print("Trying possible signatures...")

            for lag in [
                np.zeros(0),
                np.ones(1),
            ]:
                try:
                    H = prob.hess(x, lag)
                    print(f"\nprob.hess(x, lag={lag}):")
                    print(H)
                    print("shape:", np.asarray(H).shape)
                except Exception as e:
                    print(f"\nprob.hess(x, lag={lag}) ERROR:")
                    print(repr(e))

    except Exception as e:
        print("\nProblem Hessian ERROR:")
        print(repr(e))


    try:
        if hasattr(prob.constraints, "hess"):
            x = np.asarray(prob.x0, dtype=float)

            print("\nTrying constraints.hess(...) directly:")

            for lag in [
                np.zeros(0),
                np.ones(1),
            ]:
                try:
                    H = prob.constraints.hess(x, lag)
                    print(f"\nconstraints.hess(x, lag={lag}):")
                    print(H)
                    print("shape:", np.asarray(H).shape)
                except Exception as e:
                    print(f"\nconstraints.hess(x, lag={lag}) ERROR:")
                    print(repr(e))

    except Exception as e:
        print("\nConstraints Hessian ERROR:")
        print(repr(e))


    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)

    hessian_inspection(prob)


def process(file_path):
    problem = pyqplib.read_problem(file_path)
    print(problem)
    x0 = problem.x0
    obj = problem.obj_val(x0)
    cons = problem.cons_val(x0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: test_pyqplib.py qplib_file_path')
    qplib_file = sys.argv[1]

    prob = pyqplib.read_problem(qplib_file)
    data = extract_qplib_data(prob)

    # examine(qplib_file)
    # process(qplib_file)

    print("Problem:", data["name"])
    print("Variables:", data["num_vars"])
    print("Constraints:", data["num_cons"])

    print("\nFirst constraint:")
    print(data["constraints"][0])

    print("\nFirst five constraints:")
    for constraint in data["constraints"][:5]:
        print(constraint)

    print("\nObjective:")
    print(data["objective"])