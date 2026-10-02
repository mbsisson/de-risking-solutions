import sys
import pyqplib

import numpy as np
import pyqplib

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
        sys.exit('usage: converter.py qplib_file_path')

    qplib_file = sys.argv[1]

    examine(qplib_file)
    # process(qplib_file)