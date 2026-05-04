# F834 Bit15 Wider Shape-Mild Closure

F833 widened the F552/F829 bit15 HW83 continuation:

- init HW: 83
- init lane: `[10, 6, 12, 14, 13, 6, 12, 10]`
- init M2 weight: 18
- objective/pair-rank: cg/cg
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- pair pool: 2048
- beam width: 1024
- max pairs/radius: 8/16

Result:

- best seen HW: 83, source init
- new records: 0
- depth best HW sequence: 92, 91, 90, 88, 89, 90, 88, 90
- wall: 1979.89s

Interpretation:

Bit15 HW83 is closed under both standard and wider shape-mild cg continuation.
The wider pool/radius changes intermediate depths but never approaches a new
record. This makes bit15 a strong current shelf under the M2 pair-beam family.

Next bit15 work should probably change coordinates, not just widen this beam:
targeted lane shaping, a different residual basis, or upstream residual/candidate
generation.
