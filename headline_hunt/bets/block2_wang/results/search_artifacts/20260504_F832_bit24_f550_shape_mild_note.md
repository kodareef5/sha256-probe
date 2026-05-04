# F832 Bit24 F550 Shape-Mild Continuation Note

F831 continued Mac's F550 bit24 F428-basis HW84 absorber with calibrated mild
shape bias:

- init HW: 84
- init lane: `[9, 7, 16, 11, 13, 8, 11, 9]`
- init M2 weight: 54
- objective/pair-rank: cg/cg
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- max pairs/radius: 6/12

Result:

- best seen HW: 84, source init
- new records: 0
- depth best HW sequence: 95, 91, 88, 91, 87, 89
- best shaped objective: HW87, objective 102.25
- best shaped-objective transition: added7/removed3/net+4, M2 weight 58
- wall: 719.72s

Interpretation:

The F550 HW84 record is closed under this mild shape-aware cg continuation. The
beam can find a balanced lower-cg state, but not one with lower total HW. This
supports treating the current absorber portfolio as locally shelved under the
standard 1024x1024 pair-beam scale, unless a wider beam, different objective, or
new upstream residual basis is introduced.
