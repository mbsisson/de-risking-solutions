\ Simple Cost-Flow Example
\ Nodes: 1 (supply 10), 4 (demand 10)
\ Arcs: (1,2), (1,3), (2,3), (2,4), (3,4)
\ costs: 2.0,   5.0,   1.0,   3.0,   2.0
\ cap.s: 10.0,  5.0,   4.0,   6.0,   10.0

Minimize
  obj: 2.0 x12 + 5.0 x13 + 1.0 x23 + 3.0 x24 + 2.0 x34

Subject To
  \ Flow Balance constraints
  Node1: x12 + x13 = 10
  Node2: x12 - x23 - x24 = 0
  Node3: x13 + x23 - x34 = 0
  Node4: x24 + x34 = 10

  \ Capacity constraints
  cap12: x12 <= 10.0
  cap13: x13 <= 5.0
  cap23: x23 <= 4.0
  cap24: x24 <= 6.0
  cap34: x34 <= 10.0

Bounds
  \ Variables non-negative

End