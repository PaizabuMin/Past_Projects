# Part (b): New Toy Traces

## Constraint Checks
- PASS: all new traces keep original length and PC values.

## Comparison
| Case | Predictor cfg | Old manual | Old mispred | New manual | New mispred | Improved |
|---|---|---:|---:|---:|---:|---|
| simple_for | T k=16 c=2 s=3 | 1/11 | 0.090909 | 0/11 | 0.000000 | YES |
| two_for | B k=16 c=2 s=4 | 2/21 | 0.095238 | 1/21 | 0.047619 | YES |
| biased_if | L k=16 c=2 s=3 | 3/18 | 0.166667 | 1/18 | 0.055556 | YES |
| even_odd_if | G k=16 c=2 s=4 | 2/23 | 0.086957 | 1/23 | 0.043478 | YES |
