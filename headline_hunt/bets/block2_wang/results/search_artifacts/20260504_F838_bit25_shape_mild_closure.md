# F838 Bit25 Shape-Mild Closure

F837 continued Mac's F562 bit25 HW84 absorber with calibrated mild shape bias:

- init HW: 84
- init lane: `[9, 11, 13, 10, 9, 9, 9, 14]`
- init M2 weight: 28
- objective/pair-rank: cg/cg
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- max pairs/radius: 6/12

Result:

- best seen HW: 84, source init
- new records: 0
- depth best HW sequence: 92, 91, 90, 89, 90, 90
- wall: 710.74s

Interpretation:

Bit25 HW84 is closed under both Mac's plain cg continuation (F562) and this
shape-mild cg continuation (F837). It remains an important portfolio member
because it ties bit24 F428-basis HW84 at much lower M2 weight, but the standard
M2 pair-beam continuation does not currently move it.

The strongest current shelves under this operator family are:

- bit13 HW82
- bit15 HW83
- bit24 F428-basis HW84
- bit25 HW84
- bit14 HW85
