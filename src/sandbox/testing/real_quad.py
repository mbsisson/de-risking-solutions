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
set I;                                             # index set for variables
set features;                                      # set of features
param phiQuadCoeffs {1..numcuts, features, I, I};  # Quadratic coefficient matrix for each cut and feature 
param phiLinCoeffs {1..numcuts, features, I};      # Linear coefficients for each cut and feature
param phiConstants {features};                     # Constant terms for each feature (cut independent)

# VARIABLES for exposure cuts
var PHI_L >= 0;                                    # Exposure variable in objective
var cutPHI_L {cut in 1..numcuts} >= 0;             # Value of each cut, largest is PHI_L
var phi {cut in 1..numcuts, features} >= 0;        # Value of phi_feature(x|z^t) for each cut, evaluated at current X

#VARIABLES
var x2 >= 0, <= 6;
var x3 >= -1, <= 1;
var x4 >= -1, <= 1;
var x5 := 1.59481484, >= 1.59481484, <= 4.40518516;
var x6 >= -1, <= 1;
var x7 >= 0, <= 1;
var x8 := 1.42893129, >= 1.42893129, <= 4.57106871;
var x9 >= -1, <= 1;
var x10 >= -1, <= 1;
var x11 := 1.52785695, >= 1.52785695, <= 4.47214305;
var x12 >= -1, <= 1;
var x13 >= -1, <= 1;
var x14 := 1.04912586, >= 1.04912586, <= 4.95087414;
var x15 := 1.59481484, >= 1.59481484, <= 8.40518516;
var x16 := 1.42893129, >= 1.42893129, <= 8.57106871;
var x17 := 1.52785695, >= 1.52785695, <= 8.47214305;
var x18 := 1.04912586, >= 1.04912586, <= 8.95087414;
var X {I};  # X = x

# OBJECTIVE with exposure term
minimize obj:    Theta*PHI_L + x2;

subject to

# CONSTRAINTS defining X
defn_X2: X[2] = x2;
defn_X3: X[3] = x3;
defn_X4: X[4] = x4;
defn_X5: X[5] = x5;
defn_X6: X[6] = x6;
defn_X7: X[7] = x7;
defn_X8: X[8] = x8;
defn_X9: X[9] = x9;
defn_X10: X[10] = x10;
defn_X11: X[11] = x11;
defn_X12: X[12] = x12;
defn_X13: X[13] = x13;
defn_X14: X[14] = x14;
defn_X15: X[15] = x15;
defn_X16: X[16] = x16;
defn_X17: X[17] = x17;
defn_X18: X[18] = x18;

# CONSTRAINTS for cuts
Phicutrep {cut in 1..numcuts}: cutPHI_L[cut] >= sum {(cut, f) in nonzero_cutweights} CutWeights[cut, f] * phi[cut, f];
Phicut {cut in 1..numcuts}: PHI_L >= cutPHI_L[cut];

# CONSTRAINTS for phi definition
phi_definition {cut in 1..numcuts, f in features}:
     phi[cut, f] = sum {i in I, j in I} X[i] * phiQuadCoeffs[cut, f, i, j] * X[j] + sum {i in I} phiLinCoeffs[cut, f, i] * X[i] + phiConstants[f];

# other CONSTRAINTS

e2:    0.20410502*x3 + 2.24629156*x4 - x5 <= 0;

e3:    3.94678752*x6 - 1.42893791*x7 - x8 <= 0;

e4:  - 1.52786255*x9 + 2.47212728*x10 - x11 <= 0;

e5:    0.43022284*x12 + 1.63415571*x13 - x14 <= 0;

e6:    3.40502701*x3 - 1.59481484*x4 - x5 <= 0;

e7:  - 6.05321248*x6 - 1.42893791*x7 - x8 <= 0;

e8:    2.47213745*x9 + 0.47212728*x10 - x11 <= 0;

e9:    1.60415853*x12 - 1.04912586*x13 - x14 <= 0;

e10:  - 4.40522266*x3 - 1.59481484*x4 - x5 <= 0;

e11:    0.19678752*x6 + 1.69606209*x7 - x8 <= 0;

e12:    3.47213745*x9 - 1.52787272*x10 - x11 <= 0;

e13:  - 3.14748592*x12 - 1.04912586*x13 - x14 <= 0;

e14:  - 1.52786255*x9 - 1.52787272*x10 - x11 <= 0;

e15:    x2 + 0.20410502*x3 + 2.24629156*x4 - x5 >= 0;

e16:    x2 + 3.94678752*x6 - 1.42893791*x7 - x8 >= 0;

e17:    x2 - 1.52786255*x9 + 2.47212728*x10 - x11 >= 0;

e18:    x2 + 0.43022284*x12 + 1.63415571*x13 - x14 >= 0;

e19:    x2 + 3.40502701*x3 - 1.59481484*x4 - x5 >= 0;

e20:    x2 - 6.05321248*x6 - 1.42893791*x7 - x8 >= 0;

e21:    x2 + 2.47213745*x9 + 0.47212728*x10 - x11 >= 0;

e22:    x2 + 1.60415853*x12 - 1.04912586*x13 - x14 >= 0;

e23:    x2 - 4.40522266*x3 - 1.59481484*x4 - x5 >= 0;

e24:    x2 + 0.19678752*x6 + 1.69606209*x7 - x8 >= 0;

e25:    x2 + 3.47213745*x9 - 1.52787272*x10 - x11 >= 0;

e26:    x2 - 3.14748592*x12 - 1.04912586*x13 - x14 >= 0;

e27:    x2 - x5 >= 0;

e28:    x2 - x8 >= 0;

e29:    x2 - 1.52786255*x9 - 1.52787272*x10 - x11 >= 0;

e30:    x2 - x14 >= 0;

e31:  - 2.24629156*x3 + 0.20410502*x4 - x15 <= 0;

e32:    1.42893791*x6 + 3.94678752*x7 - x16 <= 0;

e33:  - 2.47212728*x9 - 1.52786255*x10 - x17 <= 0;

e34:  - 1.63415571*x12 + 0.43022284*x13 - x18 <= 0;

e35:    1.59481484*x3 + 3.40502701*x4 - x15 <= 0;

e36:    1.42893791*x6 - 6.05321248*x7 - x16 <= 0;

e37:  - 0.47212728*x9 + 2.47213745*x10 - x17 <= 0;

e38:    1.04912586*x12 + 1.60415853*x13 - x18 <= 0;

e39:    1.59481484*x3 - 4.40522266*x4 - x15 <= 0;

e40:  - 1.69606209*x6 + 0.19678752*x7 - x16 <= 0;

e41:    1.52787272*x9 + 3.47213745*x10 - x17 <= 0;

e42:    1.04912586*x12 - 3.14748592*x13 - x18 <= 0;

e43:    1.52787272*x9 - 1.52786255*x10 - x17 <= 0;

e44:  - 2.24629156*x3 + 0.20410502*x4 - x15 >= -10;

e45:    1.42893791*x6 + 3.94678752*x7 - x16 >= -10;

e46:  - 2.47212728*x9 - 1.52786255*x10 - x17 >= -10;

e47:  - 1.63415571*x12 + 0.43022284*x13 - x18 >= -10;

e48:    1.59481484*x3 + 3.40502701*x4 - x15 >= -10;

e49:    1.42893791*x6 - 6.05321248*x7 - x16 >= -10;

e50:  - 0.47212728*x9 + 2.47213745*x10 - x17 >= -10;

e51:    1.04912586*x12 + 1.60415853*x13 - x18 >= -10;

e52:    1.59481484*x3 - 4.40522266*x4 - x15 >= -10;

e53:  - 1.69606209*x6 + 0.19678752*x7 - x16 >= -10;

e54:    1.52787272*x9 + 3.47213745*x10 - x17 >= -10;

e55:    1.04912586*x12 - 3.14748592*x13 - x18 >= -10;

e56:    1.52787272*x9 - 1.52786255*x10 - x17 >= -10;

e57: x3^2 + x4^2 = 1;

e58: x6^2 + x7^2 = 1;

e59: x9^2 + x10^2 = 1;

e60: x12^2 + x13^2 = 1;

e61: x5^2 - 2*x8*x5 + x8^2 + x15^2 - 2*x16*x15 + x16^2 >= 9.143040659;

e62: x5^2 - 2*x11*x5 + x11^2 + x15^2 - 2*x17*x15 + x17^2 >= 9.751079108;

e63: x5^2 - 2*x14*x5 + x14^2 + x15^2 - 2*x18*x15 + x18^2 >= 6.990422425;

e64: x5^2 - 4.5236206*x6*x5 - 1.06782914*x7*x5 - 2*x8*x5 + 5.400850601*x6^2 + 
     4.5236206*x8*x6 + 1.06782914*x15*x6 - 1.06782914*x16*x6 + 5.400850601*x7^2
      + 1.06782914*x8*x7 - 4.5236206*x15*x7 + 4.5236206*x16*x7 + x8^2 + x15^2
      - 2*x16*x15 + x16^2 >= 6.199294212;

e65: x5^2 + 4.3914795*x9*x5 - 1.47802734*x10*x5 - 2*x11*x5 + 5.367414254*x9*x9
      - 4.3914795*x11*x9 + 1.47802734*x15*x9 - 1.47802734*x17*x9 + 5.367414254*
     x10^2 + 1.47802734*x11*x10 + 4.3914795*x15*x10 - 4.3914795*x17*x10 + x11^2
      + x15^2 - 2*x17*x15 + x17^2 >= 5.681888199;

e66: x5^2 - 3.02492942*x12*x5 - 1.00827778*x13*x5 - 2*x14*x5 + 2.541705519*x12^
     2 + 3.02492942*x14*x12 + 1.00827778*x15*x12 - 1.00827778*x18*x12 + 
     2.541705519*x13^2 + 1.00827778*x14*x13 - 3.02492942*x15*x13 + 3.02492942*
     x18*x13 + x14^2 + x15^2 - 2*x18*x15 + x18^2 >= 4.578751829;

e67: x5^2 + 4.009552*x6*x5 - 1.45166714*x7*x5 - 2*x8*x5 + 4.545961182*x6^2 - 
     4.009552*x8*x6 + 1.45166714*x15*x6 - 1.45166714*x16*x6 + 4.545961182*x7^2
      + 1.45166714*x8*x7 + 4.009552*x15*x7 - 4.009552*x16*x7 + x8^2 + x15^2 - 2
     *x16*x15 + x16^2 >= 5.280432558;
"""
)

# 3. Prepare Sample Data
Theta = 10.0
numcuts = 1
features = [f"e{i}" for i in range(2, 68)]
var_indicies = list(range(2, 19))

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

# Define linear coefficients
lin_tensor = np.ones((numcuts, len(features), len(var_indicies)))
lin_data = {
    (cut + 1, features[f], var_indicies[i]): lin_tensor[cut, f, i]
    for cut in range(numcuts)
    for f in range(len(features))
    for i in range(len(var_indicies))
}

# Define constant
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
ampl.get_parameter("phiQuadCoeffs").set_values(quad_data)
ampl.get_parameter("phiLinCoeffs").set_values(lin_data)
ampl.get_parameter("phiConstants").set_values(const_data)

# 5. Print for Visual Inspection
print("=== Visual Inspection of Generated Constraints ===")
# expand() generates the explicit algebraic representation after parameter substitution
print(ampl.expand())
