# F824 M2 Shape Calibration

## Runs

- F821: F788 HW86 with strong shape bias
  - net-add penalty `1.5`, removed-bit bonus `1.0`
  - closed at HW86
- F822: F788 HW86 with mild shape bias
  - net-add penalty `0.5`, removed-bit bonus `0.25`
  - recovered HW78 at depth 6
  - transition shape: added8/removed4/net+4, M2 weight 40->44
- F823: F799 HW87 with mild shape bias
  - net-add penalty `0.5`, removed-bit bonus `0.25`
  - recovered only HW86 at depth 5
  - transition shape: added10/removed0/net+10, M2 weight 40->50

## Calibration Result

Strong shape bias is too aggressive: it suppresses the known good F788 repair.

Mild shape bias is calibrated enough to preserve the F788 HW78 path, but it
does not redirect F799 away from the pure-add overfill repair. This separates
the branches cleanly:

- F788 has a balanced repair path that survives mild shape bias.
- F799 still repairs only by pure additions under the same calibrated setting.

## Operator Consequence

Do not use strong shape penalties as the main repair beam objective. Use mild
shape bias as a branch diagnostic and selector feature:

- a candidate passes if mild shape repair improves while keeping bounded net
  additions;
- a candidate is suspect if its only improvement has high net additions and no
  removals;
- F799 fails that selector, even though it reaches HW86.

The next upstream selector should score detours by whether a calibrated mild
repair run produces F788-like transition shape, not just whether it improves HW.
