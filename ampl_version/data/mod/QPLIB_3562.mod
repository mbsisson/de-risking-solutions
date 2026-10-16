#  MIQCP written by GAMS Convert at 02/15/18 15:47:31
#  
#  Equation counts
#      Total        E        G        L        N        X        C        B
#         43        1        0       42        0        0        0        0
#  
#  Variable counts
#                   x        b        i      s1s      s2s       sc       si
#      Total     cont   binary  integer     sos1     sos2    scont     sint
#         64        1        7       56        0        0        0        0
#  FX      0        0        0        0        0        0        0        0
#  
#  Nonzero counts
#      Total    const       NL      DLL
#        288      190       98        0
# 
#  Reformulation has removed 1 variable and 1 equation


var b2 binary >= 0, <= 1;
var b3 binary >= 0, <= 1;
var b4 binary >= 0, <= 1;
var b5 binary >= 0, <= 1;
var b6 binary >= 0, <= 1;
var b7 binary >= 0, <= 1;
var b8 binary >= 0, <= 1;
var i9 integer >= 0, <= 15;
var i10 integer >= 0, <= 15;
var i11 integer >= 0, <= 15;
var i12 integer >= 0, <= 15;
var i13 integer >= 0, <= 15;
var i14 integer >= 0, <= 15;
var i15 integer >= 0, <= 15;
var i16 integer >= 0, <= 6;
var i17 integer >= 0, <= 6;
var i18 integer >= 0, <= 6;
var i19 integer >= 0, <= 6;
var i20 integer >= 0, <= 6;
var i21 integer >= 0, <= 6;
var i22 integer >= 0, <= 6;
var i23 integer >= 0, <= 6;
var i24 integer >= 0, <= 6;
var i25 integer >= 0, <= 6;
var i26 integer >= 0, <= 6;
var i27 integer >= 0, <= 6;
var i28 integer >= 0, <= 6;
var i29 integer >= 0, <= 6;
var i30 integer >= 0, <= 6;
var i31 integer >= 0, <= 6;
var i32 integer >= 0, <= 6;
var i33 integer >= 0, <= 6;
var i34 integer >= 0, <= 6;
var i35 integer >= 0, <= 6;
var i36 integer >= 0, <= 6;
var i37 integer >= 0, <= 6;
var i38 integer >= 0, <= 6;
var i39 integer >= 0, <= 6;
var i40 integer >= 0, <= 6;
var i41 integer >= 0, <= 6;
var i42 integer >= 0, <= 6;
var i43 integer >= 0, <= 6;
var i44 integer >= 0, <= 6;
var i45 integer >= 0, <= 6;
var i46 integer >= 0, <= 6;
var i47 integer >= 0, <= 6;
var i48 integer >= 0, <= 6;
var i49 integer >= 0, <= 6;
var i50 integer >= 0, <= 6;
var i51 integer >= 0, <= 6;
var i52 integer >= 0, <= 6;
var i53 integer >= 0, <= 6;
var i54 integer >= 0, <= 6;
var i55 integer >= 0, <= 6;
var i56 integer >= 0, <= 6;
var i57 integer >= 0, <= 6;
var i58 integer >= 0, <= 6;
var i59 integer >= 0, <= 6;
var i60 integer >= 0, <= 6;
var i61 integer >= 0, <= 6;
var i62 integer >= 0, <= 6;
var i63 integer >= 0, <= 6;
var i64 integer >= 0, <= 6;

minimize obj:    0.1*b2 + 0.2*b3 + 0.3*b4 + 0.4*b5 + 0.5*b6 + 0.6*b7 + 0.7*b8
     + i9 + i10 + i11 + i12 + i13 + i14 + i15;

subject to

e2:    550*i16 + 630*i17 + 685*i18 + 720*i19 + 760*i20 + 810*i21 + 850*i22
     <= 3400;

e3:    550*i23 + 630*i24 + 685*i25 + 720*i26 + 760*i27 + 810*i28 + 850*i29
     <= 3400;

e4:    550*i30 + 630*i31 + 685*i32 + 720*i33 + 760*i34 + 810*i35 + 850*i36
     <= 3400;

e5:    550*i37 + 630*i38 + 685*i39 + 720*i40 + 760*i41 + 810*i42 + 850*i43
     <= 3400;

e6:    550*i44 + 630*i45 + 685*i46 + 720*i47 + 760*i48 + 810*i49 + 850*i50
     <= 3400;

e7:    550*i51 + 630*i52 + 685*i53 + 720*i54 + 760*i55 + 810*i56 + 850*i57
     <= 3400;

e8:    550*i58 + 630*i59 + 685*i60 + 720*i61 + 760*i62 + 810*i63 + 850*i64
     <= 3400;

e9:  - 550*i16 - 630*i17 - 685*i18 - 720*i19 - 760*i20 - 810*i21 - 850*i22
     <= -3200;

e10:  - 550*i23 - 630*i24 - 685*i25 - 720*i26 - 760*i27 - 810*i28 - 850*i29
      <= -3200;

e11:  - 550*i30 - 630*i31 - 685*i32 - 720*i33 - 760*i34 - 810*i35 - 850*i36
      <= -3200;

e12:  - 550*i37 - 630*i38 - 685*i39 - 720*i40 - 760*i41 - 810*i42 - 850*i43
      <= -3200;

e13:  - 550*i44 - 630*i45 - 685*i46 - 720*i47 - 760*i48 - 810*i49 - 850*i50
      <= -3200;

e14:  - 550*i51 - 630*i52 - 685*i53 - 720*i54 - 760*i55 - 810*i56 - 850*i57
      <= -3200;

e15:  - 550*i58 - 630*i59 - 685*i60 - 720*i61 - 760*i62 - 810*i63 - 850*i64
      <= -3200;

e16:    i16 + i17 + i18 + i19 + i20 + i21 + i22 <= 6;

e17:    i23 + i24 + i25 + i26 + i27 + i28 + i29 <= 6;

e18:    i30 + i31 + i32 + i33 + i34 + i35 + i36 <= 6;

e19:    i37 + i38 + i39 + i40 + i41 + i42 + i43 <= 6;

e20:    i44 + i45 + i46 + i47 + i48 + i49 + i50 <= 6;

e21:    i51 + i52 + i53 + i54 + i55 + i56 + i57 <= 6;

e22:    i58 + i59 + i60 + i61 + i62 + i63 + i64 <= 6;

e23:    b2 - i9 <= 0;

e24:    b3 - i10 <= 0;

e25:    b4 - i11 <= 0;

e26:    b5 - i12 <= 0;

e27:    b6 - i13 <= 0;

e28:    b7 - i14 <= 0;

e29:    b8 - i15 <= 0;

e30:  - 15*b2 + i9 <= 0;

e31:  - 15*b3 + i10 <= 0;

e32:  - 15*b4 + i11 <= 0;

e33:  - 15*b5 + i12 <= 0;

e34:  - 15*b6 + i13 <= 0;

e35:  - 15*b7 + i14 <= 0;

e36:  - 15*b8 + i15 <= 0;

e37: (-i16*i9) - i23*i10 - i30*i11 - i37*i12 - i44*i13 - i51*i14 - i58*i15
      <= -8;

e38: (-i17*i9) - i24*i10 - i31*i11 - i38*i12 - i45*i13 - i52*i14 - i59*i15
      <= -11;

e39: (-i18*i9) - i25*i10 - i32*i11 - i39*i12 - i46*i13 - i53*i14 - i60*i15
      <= -15;

e40: (-i19*i9) - i26*i10 - i33*i11 - i40*i12 - i47*i13 - i54*i14 - i61*i15
      <= -5;

e41: (-i20*i9) - i27*i10 - i34*i11 - i41*i12 - i48*i13 - i55*i14 - i62*i15
      <= -8;

e42: (-i21*i9) - i28*i10 - i35*i11 - i42*i12 - i49*i13 - i56*i14 - i63*i15
      <= -12;

e43: (-i22*i9) - i29*i10 - i36*i11 - i43*i12 - i50*i13 - i57*i14 - i64*i15
      <= -6;
