# F841 Bit6 Shape-Mild Closure

F839/F840 checked Mac's new bit6 HW85 branch.

## F839 Transition Shape

Mac's F564 bit6 cg step:

- HW: 87->85
- M2 weight: 10->18
- transition shape: added8/removed0/net+8
- cover shape: four add-add pairs

This is another absorber-growth transition, not balanced mature repair.

## F840 Shape-Mild Continuation

F840 continued the HW85 endpoint with calibrated mild shape bias:

- init lane: `[9, 13, 12, 13, 8, 7, 14, 9]`
- objective/pair-rank: cg/cg
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- max pairs/radius: 6/12

Result:

- best seen HW: 85, source init
- new records: 0
- depth best HW sequence: 93, 91, 91, 88, 87, 89
- best shaped objective: HW88, objective 107.5
- best shaped-objective transition: added6/removed2/net+4, M2 weight 22
- wall: 730.43s

Interpretation:

Bit6 now joins the HW85 tier, but it is also closed under both plain cg and
shape-mild cg continuation at the standard beam scale. The mature-shelf pattern
continues: shape-aware cg can find balanced pressure-relief states, but those
states do not currently convert into lower total HW.
