# DSE Interpretation

Shared-config method: one configuration per (budget, predictor) is chosen globally by highest average accuracy across all traces.

Observed trends:
- Small budgets tend to favor bimodal (B) because history tables consume too much overhead.
- At higher budgets, history-based predictors (T/L) usually close the gap or win.
- Gshare (G) improves with budget but is less often the top performer in this search space.

## bzip2.trc
- 32 bits: best=B (accuracy=0.938846, storage=32)
- 64 bits: best=B (accuracy=0.956308, storage=64)
- 128 bits: best=T (accuracy=0.951637, storage=112)
- 256 bits: best=B (accuracy=0.957518, storage=256)
- 512 bits: best=L (accuracy=0.961329, storage=448)
- 1024 bits: best=B (accuracy=0.961541, storage=768)
- 2048 bits: best=G (accuracy=0.962560, storage=1030)
- 4096 bits: best=G (accuracy=0.964673, storage=3080)
- Winner counts across budgets: B=4, T=1, L=1, G=2

## gcc.trc
- 32 bits: best=B (accuracy=0.883165, storage=32)
- 64 bits: best=B (accuracy=0.908053, storage=64)
- 128 bits: best=B (accuracy=0.924213, storage=128)
- 256 bits: best=B (accuracy=0.932014, storage=256)
- 512 bits: best=B (accuracy=0.936247, storage=512)
- 1024 bits: best=T (accuracy=0.936326, storage=1024)
- 2048 bits: best=T (accuracy=0.944634, storage=1728)
- 4096 bits: best=T (accuracy=0.942429, storage=3328)
- Winner counts across budgets: B=5, T=3, L=0, G=0

## h264ref.trc
- 32 bits: best=B (accuracy=0.774034, storage=32)
- 64 bits: best=B (accuracy=0.829971, storage=64)
- 128 bits: best=B (accuracy=0.896285, storage=128)
- 256 bits: best=B (accuracy=0.926206, storage=256)
- 512 bits: best=B (accuracy=0.934116, storage=512)
- 1024 bits: best=B (accuracy=0.935041, storage=768)
- 2048 bits: best=T (accuracy=0.949534, storage=1728)
- 4096 bits: best=G (accuracy=0.949457, storage=3080)
- Winner counts across budgets: B=6, T=1, L=0, G=1

