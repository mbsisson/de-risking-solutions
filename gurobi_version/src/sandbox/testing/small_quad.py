import numpy as np
from amplpy import AMPL

# 1. Initialize AMPL
ampl = AMPL()

# 2. Define the AMPL Model
ampl.eval(
"""
# PARAMETERS for exposure cuts
param Theta;
param numcuts;
set nonzero_cutweights dimen 2;  # cut num, feature num
param CutWeights {nonzero_cutweights};

# PARAMETERS for phi definitions
set I;  #index set for variables
set features;
param phiQuadCoeffs {1..numcuts, features, I, I};  # Quadratic coefficient matrix for each cut and feature 
param phiLinCoeffs {1..numcuts, features, I};          # Linear coefficients for each cut and feature
param phiConstants {features};                           # Constant terms for each feature (cut independent)

# PARAMETERS for variable definitions
param lb {I};
param ub {I};

# VARIABLES for exposure cuts
var PHI_L >= 0;
var cutPHI_L {cut in 1..numcuts};
var phi {cut in 1..numcuts, features} >= 0;

# VARIABLES
var x {i in I} >= lb[i], <= ub[i];

# OBJECTIVE with exposure term
minimize obj:    Theta*PHI_L + x[2];

subject to

# CONSTRAINTS for cuts
Phicutrep {cut in 1..numcuts}: cutPHI_L[cut] >= sum {(cut,f) in nonzero_cutweights} CutWeights[cut,f] * phi[cut, f];
Phicut {cut in 1..numcuts}: PHI_L >= cutPHI_L[cut];

# CONSTRAINTS for phi definition
phi_definition {cut in 1..numcuts, f in features}:
     phi[cut ,f] = sum {i in I, j in I} x[i] * phiQuadCoeffs[cut, f, i, j] * x[j] + sum {i in I} phiLinCoeffs[cut, f, i] * x[i] + phiConstants[f];

# other CONSTRAINTS

e2:    0.20410502*x[3] + 2.24629156*x[4] - x[5] <= 0;

e57: x[3]^2 + x[4]^2 = 1;

e61: x[5]^2 - 2*x[8]*x[5] + x[8]^2 + x[15]^2 - 2*x[16]*x[15] + x[16]^2 >= 9.143040659;

e64: x[5]^2 - 4.5236206*x[6]*x[5] - 1.06782914*x[7]*x[5] - 2*x[8]*x[5] + 5.400850601*x[6]^2 + 
     4.5236206*x[8]*x[6] + 1.06782914*x[15]*x[6] - 1.06782914*x[16]*x[6] + 5.400850601*x[7]^2
      + 1.06782914*x[8]*x[7] - 4.5236206*x[15]*x[7] + 4.5236206*x[16]*x[7] + x[8]^2 + x[15]^2
      - 2*x[16]*x[15] + x[16]^2 >= 6.199294212;
"""
)

# 3. Prepare Sample Data
Theta = 10.0
numcuts = 1
features = [f"e{i}" for i in [2, 57, 61, 64]]
print("features: ", features)
var_indicies = list(range(2, 19))
print("vars: ", var_indicies)

# Define upper and lower bounds
ub = {
    2: 6.0,
    3: 1.0,
    4: 1.0,
    5: 4.40518516,
    6: 1.0,
    7: 1.0,
    8: 4.57106871,
    9: 1.0,
    10: 1.0,
    11: 4.47214305,
    12: 1.0,
    13: 1.0,
    14: 4.95087414,
    15: 8.40518516,
    16: 8.57106871,
    17: 8.47214305,
    18: 8.95087414
}
lb = {
    2: 0.0,
    3: -1.0,
    4: -1.0,
    5: 1.59481484,
    6: -1.0,
    7: 0.0,
    8: 1.42893129,
    9: -1.0,
    10: -1.0,
    11: 1.52785695,
    12: -1.0,
    13: -1.0,
    14: 1.04912586,
    15: 1.59481484,
    16: 1.42893129,
    17: 1.52785695,
    18: 1.04912586
}

# Define cut(s)
nonzero_cutweights = [(1, "e2"), (1, "e64")]
cutweights = {
    nonzero_cutweights[0]: .2,
    nonzero_cutweights[1]: .8
}

# Define a symmetric positive semi-definite matrix Q
quad_tensor = np.ones((numcuts, len(features), len(var_indicies), len(var_indicies)))
quad_data = {
    (cut + 1, features[f], var_indicies[i], var_indicies[j]): quad_tensor[cut, f, i, j]
    for cut in range(numcuts)
    for f in range(len(features))
    for i in range(len(var_indicies))
    for j in range(len(var_indicies))
}

# Define linear coefficients and constant
lin_tensor = np.ones((numcuts, len(features), len(var_indicies)))
lin_data = {
    (cut + 1, features[f], var_indicies[i]): lin_tensor[cut, f, i]
    for cut in range(numcuts)
    for f in range(len(features))
    for i in range(len(var_indicies))
}

const_tensor = np.ones(len(features))
const_data = {
    (features[f]): const_tensor[f]
    for f in range(len(features))
}


# 4. Populate AMPL Parameters
ampl.get_parameter("Theta").set(Theta)
ampl.get_parameter("numcuts").set(numcuts)
ampl.get_set("nonzero_cutweights").set_values(nonzero_cutweights)
ampl.get_parameter("CutWeights").set_values(cutweights)

ampl.get_set("I").set_values(var_indicies)
ampl.get_set("features").set_values(features)

ampl.get_parameter("lb").set_values(lb)
ampl.get_parameter("ub").set_values(ub)

ampl.get_parameter("phiQuadCoeffs").set_values(quad_data)
ampl.get_parameter("phiLinCoeffs").set_values(lin_data)
ampl.get_parameter("phiConstants").set_values(const_data)

# 5. Print for Visual Inspection
print("=== Visual Inspection of Generated Constraints ===")
# expand() generates the explicit algebraic representation after parameter substitution
print(ampl.expand())
