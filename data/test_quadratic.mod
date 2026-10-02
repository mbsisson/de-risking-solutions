set I; # Index set for the variables

param Q {I, I}; # Quadratic coefficient matrix
param c {I};    # Linear coefficients
param d;        # Constant term

var x {I};      # Decision variables

minimize obj:    x[1];

subject to Generic_Quadratic_Constraint:
    sum {i in I, j in I} x[i] * Q[i,j] * x[j] + sum {i in I} c[i] * x[i] + d <= 0;
