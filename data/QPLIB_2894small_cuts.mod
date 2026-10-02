#  QCP written by GAMS Convert at 02/15/18 15:46:29
#  
#  Equation counts
#      Total        E        G        L        N        X        C        B
#        210        5      179       26        0        0        0        0
#  
#  Variable counts
#                   x        b        i      s1s      s2s       sc       si
#      Total     cont   binary  integer     sos1     sos2    scont     sint
#         18       18        0        0        0        0        0        0
#  FX      0        0        0        0        0        0        0        0
#  
#  Nonzero counts
#      Total    const       NL      DLL
#       1265      177     1088        0
# 
#  Reformulation has removed 1 variable and 1 equation

# PARAMETERS for exposure cuts
set cutnonzeros dimen 2;  # cut num, feature num
param CutWeights {cutnonzeros};
param numcuts;
param Theta;

#set features;    # Index set for the features
#set I;           # Index set for the variables
#param numcuts;
#param Q {1..numcuts, features, I, I};  # Quadratic coefficient matrix for each cut and feature 
#param c {1..numcuts, features, I};     # Linear coefficients for each cut and feature
#param d {features};                    # Constant terms for each feature (cut independent)
#subject to Generic_Quadratic_Constraint {k in 1..numcuts, f in features}:
#    sum {i in I, j in I} x[i] * Q[k, f, i, j] * x[j] + sum {i in I} c[k, f, i] * x[i] + d[f] >= 0;

# PARAMETERS for variable definitions
param lb {I};
param ub {I};
param xinit {I};

# PARAMETERS for phi definitions
param numfeats;
param numvars;
param phiQuadCoeffs {1..numcuts, 1..numfeats, 1..numvars, 1..numvars};  # Quadratic coefficient matrix for each cut and feature 
param phiLinCoeffs {1..numcuts, 1..numfeats, 1..numvars};               # Linear coefficients for each cut and feature
param phiConstants {1..numfeats};                                       # Constant terms for each feature (cut independent)

# VARIABLES for exposure cuts
var PHI_L >= 0;
var cutPHI_L {i in 1..numcuts};
var phi >= 0;

# VARIABLES
var x {i in I} >= lb[i], <= ub[i];

#VARIABLES
var x2 >= 0, <= 6;
var x3 >= -1, <= 1;
var x4 >= -1, <= 1;
var x5 >= 1.59481484, <= 4.40518516;
var x6 >= -1, <= 1;
var x7 >= 0, <= 1;
var x8  >= 1.42893129, <= 4.57106871;
var x9 >= -1, <= 1;
var x10 >= -1, <= 1;
var x11 >= 1.52785695, <= 4.47214305;
var x12 >= -1, <= 1;
var x13 >= -1, <= 1;
var x14 >= 1.04912586, <= 4.95087414;
var x15 >= 1.59481484, <= 8.40518516;
var x16 >= 1.42893129, <= 8.57106871;
var x17 >= 1.52785695, <= 8.47214305;
var x18  >= 1.04912586, <= 8.95087414;

# OBJECTIVE with exposure term
minimize obj:    Theta*PHI_L + x2;

subject to

# CONSTRAINTS for cuts
Phicutrep {i in 1..numcuts}: cutPHI_L[i] >= sum {(i,j) in cutnonzeros} MatrixValue[i,j] * phi;
Phicut {i in 1..numcuts}: PHI_L >= cutPHI_L[i];

# CONSTRAINTS for phi definition
phi_definition {cut in 1..numcuts, f in 1..numfeats}:
     phi = sum {i in 1..numvars, j in 1..numvars} x[i] * phiQuadCoeffs[cut, f, i, j] * x[j]
            + sum {i in 1..numvars} phiLinCoeffs[cut, f, i] * x[i] 
            + phiConstants[f];

# other CONSTRAINTS

e2:    0.20410502*x[3] + 2.24629156*x[4] - x[5] <= 0;

e57: x[3]^2 + x[4]^2 = 1;

e61: x[5]^2 - 2*x[8]*x[5] + x[8]^2 + x[15]^2 - 2*x[16]*x[15] + x[16]^2 >= 9.143040659;

e64: x[5]^2 - 4.5236206*x[6]*x[5] - 1.06782914*x[7]*x[5] - 2*x[8]*x[5] + 5.400850601*x[6]^2 + 
     4.5236206*x[8]*x[6] + 1.06782914*x[15]*x[6] - 1.06782914*x[16]*x[6] + 5.400850601*x[7]^2
      + 1.06782914*x[8]*x[7] - 4.5236206*x[15]*x[7] + 4.5236206*x[16]*x[7] + x[8]^2 + x[15]^2
      - 2*x[16]*x[15] + x[16]^2 >= 6.199294212;
