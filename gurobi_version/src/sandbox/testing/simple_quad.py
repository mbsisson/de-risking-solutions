import numpy as np
from amplpy import AMPL

# 1. Initialize AMPL
ampl = AMPL()

# 2. Define the AMPL Model
# We use a multi-line string to define the exact model discussed
ampl.eval(
"""
set features;    # Index set for the features
set I;           # Index set for the variables

param numcuts;
param Q {1..numcuts, features, I, I};  # Quadratic coefficient matrix for each cut and feature 
param c {1..numcuts, features, I};     # Linear coefficients for each cut and feature
param d {features};                    # Constant terms for each feature (cut independent)

var x {I};      # Decision variables

minimize obj:    x[2];

subject to Generic_Quadratic_Constraint {k in 1..numcuts, f in features}:
    sum {i in I, j in I} x[i] * Q[k, f, i, j] * x[j] + sum {i in I} c[k, f, i] * x[i] + d[f] >= 0;
"""
)

# 3. Prepare Sample Data
numcuts = 2
features = [1, 2]
indices = [2, 3]

# Define a symmetric positive semi-definite matrix Q
Q_tensor = np.array([[[[2.0, 0.5, 0.0], [0.5, 3.0, 1.0], [0.0, 1.0, 4.0]],    #cut1, feat1
                      [[1.0, 1.5, 0.5], [1.5, 0.0, 2.0], [0.5, 2.0, 3.0]]],   #cut1, feat2
                     [[[2.1, 0.4, 0.0], [0.4, 3.2, 0.9], [0.0, 0.9, 4.1]],    #cut2, feat1
                      [[1.1, 1.4, 0.5], [1.4, 0.2, 1.2], [0.5, 1.2, 3.2]]]])  #cut2, feat2

Q_data = {
    (cut + 1, features[f], indices[i], indices[j]): Q_tensor[cut, f, i, j]
    for cut in range(numcuts)
    for f in range(len(features))
    for i in range(len(indices))
    for j in range(len(indices))
}

# Define linear coefficients and constant
c_tensor = np.array([[[-1.0, 2.5, 0.0],    #cut1, feat1
                      [0.0, 1.5, 0.5]],   #cut1, feat2
                     [[-0.9, 2.6, 0.1],    #cut2, feat1
                      [0.1, 1.3, 0.6]]])  #cut2, feat2
c_data = {
    (cut + 1, features[f], indices[i]): c_tensor[cut, f, i]
    for cut in range(numcuts)
    for f in range(len(features))
    for i in range(len(indices))
}

d_data = {1:-10.5, 2:-5.1}

# 4. Populate AMPL Parameters
ampl.get_set("I").set_values(indices)
ampl.get_set("features").set_values(features)
ampl.get_parameter("numcuts").set(numcuts)
ampl.get_parameter("Q").set_values(Q_data)
ampl.get_parameter("c").set_values(c_data)
ampl.get_parameter("d").set_values(d_data)

# 5. Print for Visual Inspection
print("=== Visual Inspection of Generated Constraints ===")
# expand() generates the explicit algebraic representation after parameter substitution
ampl.eval("expand Generic_Quadratic_Constraint;")
