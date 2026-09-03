\ Fake blending LP

Minimize
 obj: 5.2 x1 + 4.8 x2 + 6.1 x3 + 5.5 x4 + 4.9 x5
    + 6.5 x6 + 5.8 x7 + 4.6 x8 + 5.1 x9 + 6.2 x10

Subject To
 \ Demand constraints (must produce enough total product)
 demand_total:
    x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 >= 100

 \ Product-specific demand (e.g., different markets)
 demand_A:
    0.8 x1 + 0.6 x2 + 0.7 x3 + 0.9 x4 + 0.5 x5
  + 0.6 x6 + 0.7 x7 + 0.8 x8 + 0.6 x9 + 0.7 x10 >= 65
 demand_B:
    0.5 x1 + 0.7 x2 + 0.6 x3 + 0.4 x4 + 0.8 x5
  + 0.7 x6 + 0.6 x7 + 0.5 x8 + 0.7 x9 + 0.6 x10 >= 55

 \ Quality constraints
 quality_1:
    0.92 x1 + 0.88 x2 + 0.95 x3 + 0.90 x4 + 0.87 x5
  + 0.93 x6 + 0.89 x7 + 0.91 x8 + 0.88 x9 + 0.94 x10 >= 90
 quality_2:
    0.55 x1 + 0.60 x2 + 0.58 x3 + 0.62 x4 + 0.57 x5
  + 0.59 x6 + 0.61 x7 + 0.56 x8 + 0.60 x9 + 0.58 x10 >= 58
 quality_3:
    1.2 x1 + 1.0 x2 + 1.3 x3 + 1.1 x4 + 0.9 x5
  + 1.25 x6 + 1.05 x7 + 1.15 x8 + 1.0 x9 + 1.2 x10 >= 110

 \ Resource constraints
 capacity_1:
    x1 + x2 + x3 <= 60
 capacity_2:
    x4 + x5 + x6 <= 50
 capacity_3:
    x7 + x8 + x9 + x10 <= 70

Bounds
 0 <= x1 <= 40
 0 <= x2 <= 40
 0 <= x3 <= 40
 0 <= x4 <= 40
 0 <= x5 <= 40
 0 <= x6 <= 40
 0 <= x7 <= 40
 0 <= x8 <= 40
 0 <= x9 <= 40
 0 <= x10 <= 40

End