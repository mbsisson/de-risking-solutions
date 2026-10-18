###snapshot-version: 0.1.6
###model-start
var x2 >= 0
     <= 300;
var x3 >= 0
     <= 300;
var x4 >= 0.85
     <= 1
    := 0.85;
var x5 >= 0.85
     <= 1
    := 0.85;
var x6 >= 0.85
     <= 1
    := 0.85;
var x7 >= 0.85
     <= 1
    := 0.85;
var b8 binary >= 0
     <= 1;
var b9 binary >= 0
     <= 1;
var x10 >= 0
     <= 100;
var x11 >= 0
     <= 100;
var x12 >= 0
     <= 100;
var x13 >= 0
     <= 100;
var x14 >= 0
     <= 100;
var x15 >= 0
     <= 100;
var x16 >= 0
     <= 1;
var x17 >= 0
     <= 1;
var x18 >= 0
     <= 1;
var x19 >= 0
     <= 1;
var x20 >= 0
     <= 300;
var x21 >= 0
     <= 300;
var x22 >= 0;
var x23 >= 0;
var x24 >= 0
     <= 300;
var x25 >= 0
     <= 300;
var x26 >= 0
     <= 300;
var x27 >= 0
     <= 300;
var x28 >= 0
     <= 300;
var x29 >= 0
     <= 300;
var x30 >= 0
     <= 300;
var x31 >= 0
     <= 300;
var x32 >= 0
     <= 300;
var x33 >= 0
     <= 300;
var x34 >= 0
     <= 300;
var x35 >= 0
     <= 300;
var x36 >= 0
     <= 300;
var x37 >= 0
     <= 300;
var x38 >= 0
     <= 1;
var x39 >= 0
     <= 1;
var x40 >= 0
     <= 1;
var x41 >= 0
     <= 1;
var x42 >= 0
     <= 1;
var x43 >= 0
     <= 1;
var x44 >= 0
     <= 1;
var x45 >= 0
     <= 1;
var x46 >= 0
     <= 1;
var x47 >= 0
     <= 1;
var x48 >= 0
     <= 1;
var x49 >= 0
     <= 1;
minimize obj: 0.0093514*x2*x4 - 0.0139904*x2 + 0.0077308*x2*x5 - 0.0005719*x2*
  x16 + 0.0042656*x2*x17 + 0.0338147*x3*x6 - 0.0661588*x3 + 0.0373349*x3*x7 +
  0.0016371*x3*x18 + 0.0288996*x3*x19 + 0.23947*b8 + 0.75835*b9;
subject to e2: x20 + x21 + x22 + x23 == 300;
subject to e3: x24 - x25 - x26 == 0;
subject to e4: x27 - x28 - x29 - x30 == 0;
subject to e5: x31 - x32 - x33 - x34 == 0;
subject to e6: x35 - x36 - x37 == 0;
subject to e7: x38 + x39 == 1;
subject to e8: x40 + x41 + x42 == 1;
subject to e9: x43 + x44 + x45 == 1;
subject to e10: x46 + x47 == 1;
subject to e11: x16 + x17 + x48 == 1;
subject to e12: x18 + x19 + x49 == 1;
subject to e13: x2 - 300*b8 <= 0;
subject to e14: x3 - 300*b9 <= 0;
subject to e15: -(x43*x32) + x10 - 0.3333333333*x20 == 0;
subject to e16: -(x44*x32) + x11 - 0.3333333333*x20 == 0;
subject to e17: -(x45*x32) + x12 - 0.3333333333*x20 == 0;
subject to e18: -(x40*x28) + x13 - 0.3333333333*x21 == 0;
subject to e19: -(x41*x28) + x14 - 0.3333333333*x21 == 0;
subject to e20: -(x42*x28) + x15 - 0.3333333333*x21 == 0;
subject to e21: -(x38*x24) - x40*x27 + x10 == 0;
subject to e22: -(x39*x24) - x41*x27 + x11 == 0;
subject to e23: -(x42*x27) + x12 == 0;
subject to e24: -(x43*x31) + x13 == 0;
subject to e25: -(x44*x31) - x46*x35 + x14 == 0;
subject to e26: -(x45*x31) - x47*x35 + x15 == 0;
subject to e27: x38*x25 + x40*x29 + x43*x33 + 0.3333333333*x22 == 80;
subject to e28: x39*x25 + x41*x29 + x44*x33 + x46*x36 + 0.3333333333*x22
   == 30;
subject to e29: x42*x29 + x45*x33 + x47*x36 + 0.3333333333*x22 == 20;
subject to e30: x38*x26 + x40*x30 + x43*x34 + 0.3333333333*x23 == 20;
subject to e31: x39*x26 + x41*x30 + x44*x34 + x46*x37 + 0.3333333333*x23
   == 70;
subject to e32: x42*x30 + x45*x34 + x47*x37 + 0.3333333333*x23 == 80;
subject to e33: x16*x2 - x10 == 0;
subject to e34: x17*x2 - x11 == 0;
subject to e35: x48*x2 - x12 == 0;
subject to e36: x18*x3 - x13 == 0;
subject to e37: x19*x3 - x14 == 0;
subject to e38: x49*x3 - x15 == 0;
subject to e39: x10*x4 - x38*x24 == 0;
subject to e40: x11*x5 - x41*x27 == 0;
subject to e41: x14*x6 - x44*x31 == 0;
subject to e42: x15*x7 - x47*x35 == 0;
param Theta;
param numcuts;
set nonzero_cutweights dimen 2;
param cutweights{nonzero_cutweights};
set var_inds;
set features;
set nonzero_phiQuadWeights dimen 4;
param phiQuadWeights{nonzero_phiQuadWeights};
set nonzero_phiLinWeights dimen 3;
param phiLinWeights{nonzero_phiLinWeights};
param phiConstWeights{nonzero_cutweights};
param phiMinusToggle{nonzero_cutweights};
var PHI_L >= 0;
var cutPHI_L{cut in 1 .. numcuts}  >= 0;
var phi{cut in 1 .. numcuts, features}  >= 0;
var X{var_inds};
subject to defn_X2: X[2] == x2;
subject to defn_X3: X[3] == x3;
subject to defn_X4: X[4] == x4;
subject to defn_X5: X[5] == x5;
subject to defn_X6: X[6] == x6;
subject to defn_X7: X[7] == x7;
subject to defn_X8: X[8] == b8;
subject to defn_X9: X[9] == b9;
subject to defn_X10: X[10] == x10;
subject to defn_X11: X[11] == x11;
subject to defn_X12: X[12] == x12;
subject to defn_X13: X[13] == x13;
subject to defn_X14: X[14] == x14;
subject to defn_X15: X[15] == x15;
subject to defn_X16: X[16] == x16;
subject to defn_X17: X[17] == x17;
subject to defn_X18: X[18] == x18;
subject to defn_X19: X[19] == x19;
subject to defn_X20: X[20] == x20;
subject to defn_X21: X[21] == x21;
subject to defn_X22: X[22] == x22;
subject to defn_X23: X[23] == x23;
subject to defn_X24: X[24] == x24;
subject to defn_X25: X[25] == x25;
subject to defn_X26: X[26] == x26;
subject to defn_X27: X[27] == x27;
subject to defn_X28: X[28] == x28;
subject to defn_X29: X[29] == x29;
subject to defn_X30: X[30] == x30;
subject to defn_X31: X[31] == x31;
subject to defn_X32: X[32] == x32;
subject to defn_X33: X[33] == x33;
subject to defn_X34: X[34] == x34;
subject to defn_X35: X[35] == x35;
subject to defn_X36: X[36] == x36;
subject to defn_X37: X[37] == x37;
subject to defn_X38: X[38] == x38;
subject to defn_X39: X[39] == x39;
subject to defn_X40: X[40] == x40;
subject to defn_X41: X[41] == x41;
subject to defn_X42: X[42] == x42;
subject to defn_X43: X[43] == x43;
subject to defn_X44: X[44] == x44;
subject to defn_X45: X[45] == x45;
subject to defn_X46: X[46] == x46;
subject to defn_X47: X[47] == x47;
subject to defn_X48: X[48] == x48;
subject to defn_X49: X[49] == x49;
subject to Phicutrep{cut in 1 .. numcuts} : cutPHI_L[cut] >= sum{(cut,f
  ) in nonzero_cutweights} cutweights[cut,f]*phi[cut,f];
subject to Phicut{cut in 1 .. numcuts} : PHI_L >= cutPHI_L[cut];
subject to defn_phi_plus{(cut,f) in nonzero_cutweights} : phi[cut,f] >= sum
  {(cut,f,i,j) in nonzero_phiQuadWeights} X[i]*phiQuadWeights[cut,f,i,j]*X[j]
   + sum{(cut,f,i) in nonzero_phiLinWeights} phiLinWeights[cut,f,i]*X[i] +
  phiConstWeights[cut,f];
subject to defn_phi_minus{(cut,f) in nonzero_cutweights} : phi[cut,f] >= -(
  phiMinusToggle[cut,f]*(sum{(cut,f,i,j) in nonzero_phiQuadWeights} X[i]*
  phiQuadWeights[cut,f,i,j]*X[j] + sum{(cut,f,i) in nonzero_phiLinWeights}
  phiLinWeights[cut,f,i]*X[i] + phiConstWeights[cut,f]));
minimize weighted_obj: Theta*PHI_L + (0.0093514*x2*x4 + 0.0077308*x2*x5 -
  0.0005719*x2*x16 + 0.0042656*x2*x17 + 0.0338147*x3*x6 + 0.0373349*x3*x7 +
  0.0016371*x3*x18 + 0.0288996*x3*x19 - 0.0139904*x2 - 0.0661588*x3 +
  0.23947*b8 + 0.75835*b9);
###model-end

###current-problem/environment-start
problem Initial;
environ Initial;
###current-problem/environment-end

###objectives-start
objective weighted_obj;
###objectives-end

###fixes-start
###fixes-end

###drop-restore-start
###drop-restore-end

