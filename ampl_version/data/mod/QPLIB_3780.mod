#  MIQCP written by GAMS Convert at 02/15/18 15:48:14
#  
#  Equation counts
#      Total        E        G        L        N        X        C        B
#         73        1        0       72        0        0        0        0
#  
#  Variable counts
#                   x        b        i      s1s      s2s       sc       si
#      Total     cont   binary  integer     sos1     sos2    scont     sint
#        169        1       12      156        0        0        0        0
#  FX      0        0        0        0        0        0        0        0
#  
#  Nonzero counts
#      Total    const       NL      DLL
#        793      505      288        0
# 
#  Reformulation has removed 1 variable and 1 equation


var b2 binary >= 0, <= 1;
var b3 binary >= 0, <= 1;
var b4 binary >= 0, <= 1;
var b5 binary >= 0, <= 1;
var b6 binary >= 0, <= 1;
var b7 binary >= 0, <= 1;
var b8 binary >= 0, <= 1;
var b9 binary >= 0, <= 1;
var b10 binary >= 0, <= 1;
var b11 binary >= 0, <= 1;
var b12 binary >= 0, <= 1;
var b13 binary >= 0, <= 1;
var i14 integer >= 0, <= 48;
var i15 integer >= 0, <= 48;
var i16 integer >= 0, <= 48;
var i17 integer >= 0, <= 48;
var i18 integer >= 0, <= 48;
var i19 integer >= 0, <= 48;
var i20 integer >= 0, <= 48;
var i21 integer >= 0, <= 48;
var i22 integer >= 0, <= 48;
var i23 integer >= 0, <= 48;
var i24 integer >= 0, <= 48;
var i25 integer >= 0, <= 48;
var i26 integer >= 0, <= 5;
var i27 integer >= 0, <= 5;
var i28 integer >= 0, <= 5;
var i29 integer >= 0, <= 5;
var i30 integer >= 0, <= 5;
var i31 integer >= 0, <= 5;
var i32 integer >= 0, <= 5;
var i33 integer >= 0, <= 5;
var i34 integer >= 0, <= 5;
var i35 integer >= 0, <= 5;
var i36 integer >= 0, <= 5;
var i37 integer >= 0, <= 5;
var i38 integer >= 0, <= 5;
var i39 integer >= 0, <= 5;
var i40 integer >= 0, <= 5;
var i41 integer >= 0, <= 5;
var i42 integer >= 0, <= 5;
var i43 integer >= 0, <= 5;
var i44 integer >= 0, <= 5;
var i45 integer >= 0, <= 5;
var i46 integer >= 0, <= 5;
var i47 integer >= 0, <= 5;
var i48 integer >= 0, <= 5;
var i49 integer >= 0, <= 5;
var i50 integer >= 0, <= 5;
var i51 integer >= 0, <= 5;
var i52 integer >= 0, <= 5;
var i53 integer >= 0, <= 5;
var i54 integer >= 0, <= 5;
var i55 integer >= 0, <= 5;
var i56 integer >= 0, <= 5;
var i57 integer >= 0, <= 5;
var i58 integer >= 0, <= 5;
var i59 integer >= 0, <= 5;
var i60 integer >= 0, <= 5;
var i61 integer >= 0, <= 5;
var i62 integer >= 0, <= 5;
var i63 integer >= 0, <= 5;
var i64 integer >= 0, <= 5;
var i65 integer >= 0, <= 5;
var i66 integer >= 0, <= 5;
var i67 integer >= 0, <= 5;
var i68 integer >= 0, <= 5;
var i69 integer >= 0, <= 5;
var i70 integer >= 0, <= 5;
var i71 integer >= 0, <= 5;
var i72 integer >= 0, <= 5;
var i73 integer >= 0, <= 5;
var i74 integer >= 0, <= 5;
var i75 integer >= 0, <= 5;
var i76 integer >= 0, <= 5;
var i77 integer >= 0, <= 5;
var i78 integer >= 0, <= 5;
var i79 integer >= 0, <= 5;
var i80 integer >= 0, <= 5;
var i81 integer >= 0, <= 5;
var i82 integer >= 0, <= 5;
var i83 integer >= 0, <= 5;
var i84 integer >= 0, <= 5;
var i85 integer >= 0, <= 5;
var i86 integer >= 0, <= 5;
var i87 integer >= 0, <= 5;
var i88 integer >= 0, <= 5;
var i89 integer >= 0, <= 5;
var i90 integer >= 0, <= 5;
var i91 integer >= 0, <= 5;
var i92 integer >= 0, <= 5;
var i93 integer >= 0, <= 5;
var i94 integer >= 0, <= 5;
var i95 integer >= 0, <= 5;
var i96 integer >= 0, <= 5;
var i97 integer >= 0, <= 5;
var i98 integer >= 0, <= 5;
var i99 integer >= 0, <= 5;
var i100 integer >= 0, <= 5;
var i101 integer >= 0, <= 5;
var i102 integer >= 0, <= 5;
var i103 integer >= 0, <= 5;
var i104 integer >= 0, <= 5;
var i105 integer >= 0, <= 5;
var i106 integer >= 0, <= 5;
var i107 integer >= 0, <= 5;
var i108 integer >= 0, <= 5;
var i109 integer >= 0, <= 5;
var i110 integer >= 0, <= 5;
var i111 integer >= 0, <= 5;
var i112 integer >= 0, <= 5;
var i113 integer >= 0, <= 5;
var i114 integer >= 0, <= 5;
var i115 integer >= 0, <= 5;
var i116 integer >= 0, <= 5;
var i117 integer >= 0, <= 5;
var i118 integer >= 0, <= 5;
var i119 integer >= 0, <= 5;
var i120 integer >= 0, <= 5;
var i121 integer >= 0, <= 5;
var i122 integer >= 0, <= 5;
var i123 integer >= 0, <= 5;
var i124 integer >= 0, <= 5;
var i125 integer >= 0, <= 5;
var i126 integer >= 0, <= 5;
var i127 integer >= 0, <= 5;
var i128 integer >= 0, <= 5;
var i129 integer >= 0, <= 5;
var i130 integer >= 0, <= 5;
var i131 integer >= 0, <= 5;
var i132 integer >= 0, <= 5;
var i133 integer >= 0, <= 5;
var i134 integer >= 0, <= 5;
var i135 integer >= 0, <= 5;
var i136 integer >= 0, <= 5;
var i137 integer >= 0, <= 5;
var i138 integer >= 0, <= 5;
var i139 integer >= 0, <= 5;
var i140 integer >= 0, <= 5;
var i141 integer >= 0, <= 5;
var i142 integer >= 0, <= 5;
var i143 integer >= 0, <= 5;
var i144 integer >= 0, <= 5;
var i145 integer >= 0, <= 5;
var i146 integer >= 0, <= 5;
var i147 integer >= 0, <= 5;
var i148 integer >= 0, <= 5;
var i149 integer >= 0, <= 5;
var i150 integer >= 0, <= 5;
var i151 integer >= 0, <= 5;
var i152 integer >= 0, <= 5;
var i153 integer >= 0, <= 5;
var i154 integer >= 0, <= 5;
var i155 integer >= 0, <= 5;
var i156 integer >= 0, <= 5;
var i157 integer >= 0, <= 5;
var i158 integer >= 0, <= 5;
var i159 integer >= 0, <= 5;
var i160 integer >= 0, <= 5;
var i161 integer >= 0, <= 5;
var i162 integer >= 0, <= 5;
var i163 integer >= 0, <= 5;
var i164 integer >= 0, <= 5;
var i165 integer >= 0, <= 5;
var i166 integer >= 0, <= 5;
var i167 integer >= 0, <= 5;
var i168 integer >= 0, <= 5;
var i169 integer >= 0, <= 5;

minimize obj:    0.1*b2 + 0.2*b3 + 0.3*b4 + 0.4*b5 + 0.5*b6 + 0.6*b7 + 0.7*b8
     + 0.8*b9 + 0.9*b10 + b11 + 1.1*b12 + 1.2*b13 + i14 + i15 + i16 + i17 + i18
     + i19 + i20 + i21 + i22 + i23 + i24 + i25;

subject to

e2:    350*i26 + 450*i27 + 550*i28 + 650*i29 + 700*i30 + 740*i31 + 800*i32
     + 840*i33 + 910*i34 + 960*i35 + 1010*i36 + 1060*i37 <= 2100;

e3:    350*i38 + 450*i39 + 550*i40 + 650*i41 + 700*i42 + 740*i43 + 800*i44
     + 840*i45 + 910*i46 + 960*i47 + 1010*i48 + 1060*i49 <= 2100;

e4:    350*i50 + 450*i51 + 550*i52 + 650*i53 + 700*i54 + 740*i55 + 800*i56
     + 840*i57 + 910*i58 + 960*i59 + 1010*i60 + 1060*i61 <= 2100;

e5:    350*i62 + 450*i63 + 550*i64 + 650*i65 + 700*i66 + 740*i67 + 800*i68
     + 840*i69 + 910*i70 + 960*i71 + 1010*i72 + 1060*i73 <= 2100;

e6:    350*i74 + 450*i75 + 550*i76 + 650*i77 + 700*i78 + 740*i79 + 800*i80
     + 840*i81 + 910*i82 + 960*i83 + 1010*i84 + 1060*i85 <= 2100;

e7:    350*i86 + 450*i87 + 550*i88 + 650*i89 + 700*i90 + 740*i91 + 800*i92
     + 840*i93 + 910*i94 + 960*i95 + 1010*i96 + 1060*i97 <= 2100;

e8:    350*i98 + 450*i99 + 550*i100 + 650*i101 + 700*i102 + 740*i103 + 800*i104
     + 840*i105 + 910*i106 + 960*i107 + 1010*i108 + 1060*i109 <= 2100;

e9:    350*i110 + 450*i111 + 550*i112 + 650*i113 + 700*i114 + 740*i115
     + 800*i116 + 840*i117 + 910*i118 + 960*i119 + 1010*i120 + 1060*i121
     <= 2100;

e10:    350*i122 + 450*i123 + 550*i124 + 650*i125 + 700*i126 + 740*i127
      + 800*i128 + 840*i129 + 910*i130 + 960*i131 + 1010*i132 + 1060*i133
      <= 2100;

e11:    350*i134 + 450*i135 + 550*i136 + 650*i137 + 700*i138 + 740*i139
      + 800*i140 + 840*i141 + 910*i142 + 960*i143 + 1010*i144 + 1060*i145
      <= 2100;

e12:    350*i146 + 450*i147 + 550*i148 + 650*i149 + 700*i150 + 740*i151
      + 800*i152 + 840*i153 + 910*i154 + 960*i155 + 1010*i156 + 1060*i157
      <= 2100;

e13:    350*i158 + 450*i159 + 550*i160 + 650*i161 + 700*i162 + 740*i163
      + 800*i164 + 840*i165 + 910*i166 + 960*i167 + 1010*i168 + 1060*i169
      <= 2100;

e14:  - 350*i26 - 450*i27 - 550*i28 - 650*i29 - 700*i30 - 740*i31 - 800*i32
      - 840*i33 - 910*i34 - 960*i35 - 1010*i36 - 1060*i37 <= -2000;

e15:  - 350*i38 - 450*i39 - 550*i40 - 650*i41 - 700*i42 - 740*i43 - 800*i44
      - 840*i45 - 910*i46 - 960*i47 - 1010*i48 - 1060*i49 <= -2000;

e16:  - 350*i50 - 450*i51 - 550*i52 - 650*i53 - 700*i54 - 740*i55 - 800*i56
      - 840*i57 - 910*i58 - 960*i59 - 1010*i60 - 1060*i61 <= -2000;

e17:  - 350*i62 - 450*i63 - 550*i64 - 650*i65 - 700*i66 - 740*i67 - 800*i68
      - 840*i69 - 910*i70 - 960*i71 - 1010*i72 - 1060*i73 <= -2000;

e18:  - 350*i74 - 450*i75 - 550*i76 - 650*i77 - 700*i78 - 740*i79 - 800*i80
      - 840*i81 - 910*i82 - 960*i83 - 1010*i84 - 1060*i85 <= -2000;

e19:  - 350*i86 - 450*i87 - 550*i88 - 650*i89 - 700*i90 - 740*i91 - 800*i92
      - 840*i93 - 910*i94 - 960*i95 - 1010*i96 - 1060*i97 <= -2000;

e20:  - 350*i98 - 450*i99 - 550*i100 - 650*i101 - 700*i102 - 740*i103
      - 800*i104 - 840*i105 - 910*i106 - 960*i107 - 1010*i108 - 1060*i109
      <= -2000;

e21:  - 350*i110 - 450*i111 - 550*i112 - 650*i113 - 700*i114 - 740*i115
      - 800*i116 - 840*i117 - 910*i118 - 960*i119 - 1010*i120 - 1060*i121
      <= -2000;

e22:  - 350*i122 - 450*i123 - 550*i124 - 650*i125 - 700*i126 - 740*i127
      - 800*i128 - 840*i129 - 910*i130 - 960*i131 - 1010*i132 - 1060*i133
      <= -2000;

e23:  - 350*i134 - 450*i135 - 550*i136 - 650*i137 - 700*i138 - 740*i139
      - 800*i140 - 840*i141 - 910*i142 - 960*i143 - 1010*i144 - 1060*i145
      <= -2000;

e24:  - 350*i146 - 450*i147 - 550*i148 - 650*i149 - 700*i150 - 740*i151
      - 800*i152 - 840*i153 - 910*i154 - 960*i155 - 1010*i156 - 1060*i157
      <= -2000;

e25:  - 350*i158 - 450*i159 - 550*i160 - 650*i161 - 700*i162 - 740*i163
      - 800*i164 - 840*i165 - 910*i166 - 960*i167 - 1010*i168 - 1060*i169
      <= -2000;

e26:    i26 + i27 + i28 + i29 + i30 + i31 + i32 + i33 + i34 + i35 + i36 + i37
      <= 5;

e27:    i38 + i39 + i40 + i41 + i42 + i43 + i44 + i45 + i46 + i47 + i48 + i49
      <= 5;

e28:    i50 + i51 + i52 + i53 + i54 + i55 + i56 + i57 + i58 + i59 + i60 + i61
      <= 5;

e29:    i62 + i63 + i64 + i65 + i66 + i67 + i68 + i69 + i70 + i71 + i72 + i73
      <= 5;

e30:    i74 + i75 + i76 + i77 + i78 + i79 + i80 + i81 + i82 + i83 + i84 + i85
      <= 5;

e31:    i86 + i87 + i88 + i89 + i90 + i91 + i92 + i93 + i94 + i95 + i96 + i97
      <= 5;

e32:    i98 + i99 + i100 + i101 + i102 + i103 + i104 + i105 + i106 + i107
      + i108 + i109 <= 5;

e33:    i110 + i111 + i112 + i113 + i114 + i115 + i116 + i117 + i118 + i119
      + i120 + i121 <= 5;

e34:    i122 + i123 + i124 + i125 + i126 + i127 + i128 + i129 + i130 + i131
      + i132 + i133 <= 5;

e35:    i134 + i135 + i136 + i137 + i138 + i139 + i140 + i141 + i142 + i143
      + i144 + i145 <= 5;

e36:    i146 + i147 + i148 + i149 + i150 + i151 + i152 + i153 + i154 + i155
      + i156 + i157 <= 5;

e37:    i158 + i159 + i160 + i161 + i162 + i163 + i164 + i165 + i166 + i167
      + i168 + i169 <= 5;

e38:    b2 - i14 <= 0;

e39:    b3 - i15 <= 0;

e40:    b4 - i16 <= 0;

e41:    b5 - i17 <= 0;

e42:    b6 - i18 <= 0;

e43:    b7 - i19 <= 0;

e44:    b8 - i20 <= 0;

e45:    b9 - i21 <= 0;

e46:    b10 - i22 <= 0;

e47:    b11 - i23 <= 0;

e48:    b12 - i24 <= 0;

e49:    b13 - i25 <= 0;

e50:  - 48*b2 + i14 <= 0;

e51:  - 48*b3 + i15 <= 0;

e52:  - 48*b4 + i16 <= 0;

e53:  - 48*b5 + i17 <= 0;

e54:  - 48*b6 + i18 <= 0;

e55:  - 48*b7 + i19 <= 0;

e56:  - 48*b8 + i20 <= 0;

e57:  - 48*b9 + i21 <= 0;

e58:  - 48*b10 + i22 <= 0;

e59:  - 48*b11 + i23 <= 0;

e60:  - 48*b12 + i24 <= 0;

e61:  - 48*b13 + i25 <= 0;

e62: (-i26*i14) - i38*i15 - i50*i16 - i62*i17 - i74*i18 - i86*i19 - i98*i20 - 
     i110*i21 - i122*i22 - i134*i23 - i146*i24 - i158*i25 <= -10;

e63: (-i27*i14) - i39*i15 - i51*i16 - i63*i17 - i75*i18 - i87*i19 - i99*i20 - 
     i111*i21 - i123*i22 - i135*i23 - i147*i24 - i159*i25 <= -28;

e64: (-i28*i14) - i40*i15 - i52*i16 - i64*i17 - i76*i18 - i88*i19 - i100*i20 - 
     i112*i21 - i124*i22 - i136*i23 - i148*i24 - i160*i25 <= -48;

e65: (-i29*i14) - i41*i15 - i53*i16 - i65*i17 - i77*i18 - i89*i19 - i101*i20 - 
     i113*i21 - i125*i22 - i137*i23 - i149*i24 - i161*i25 <= -28;

e66: (-i30*i14) - i42*i15 - i54*i16 - i66*i17 - i78*i18 - i90*i19 - i102*i20 - 
     i114*i21 - i126*i22 - i138*i23 - i150*i24 - i162*i25 <= -40;

e67: (-i31*i14) - i43*i15 - i55*i16 - i67*i17 - i79*i18 - i91*i19 - i103*i20 - 
     i115*i21 - i127*i22 - i139*i23 - i151*i24 - i163*i25 <= -30;

e68: (-i32*i14) - i44*i15 - i56*i16 - i68*i17 - i80*i18 - i92*i19 - i104*i20 - 
     i116*i21 - i128*i22 - i140*i23 - i152*i24 - i164*i25 <= -21;

e69: (-i33*i14) - i45*i15 - i57*i16 - i69*i17 - i81*i18 - i93*i19 - i105*i20 - 
     i117*i21 - i129*i22 - i141*i23 - i153*i24 - i165*i25 <= -22;

e70: (-i34*i14) - i46*i15 - i58*i16 - i70*i17 - i82*i18 - i94*i19 - i106*i20 - 
     i118*i21 - i130*i22 - i142*i23 - i154*i24 - i166*i25 <= -8;

e71: (-i35*i14) - i47*i15 - i59*i16 - i71*i17 - i83*i18 - i95*i19 - i107*i20 - 
     i119*i21 - i131*i22 - i143*i23 - i155*i24 - i167*i25 <= -8;

e72: (-i36*i14) - i48*i15 - i60*i16 - i72*i17 - i84*i18 - i96*i19 - i108*i20 - 
     i120*i21 - i132*i22 - i144*i23 - i156*i24 - i168*i25 <= -9;

e73: (-i37*i14) - i49*i15 - i61*i16 - i73*i17 - i85*i18 - i97*i19 - i109*i20 - 
     i121*i21 - i133*i22 - i145*i23 - i157*i24 - i169*i25 <= -8;
