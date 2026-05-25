# F844 Portfolio Lane Transfer Note

F842 summarized lane distances across the current absorber portfolio.

Key lanes:

- bit13 HW82: `[10, 11, 9, 12, 9, 7, 10, 14]`
- bit15 HW83: `[10, 6, 12, 14, 13, 6, 12, 10]`
- bit25 HW84: `[9, 11, 13, 10, 9, 9, 9, 14]`
- bit6 HW85: `[9, 13, 12, 13, 8, 7, 14, 9]`

The closest top-shelf lane pair is bit25 to bit13:

- bit25 HW84 to bit13 HW82 lane L1: 10
- bit25 M2 weight: 28
- bit13 M2 weight: 29

F843 tested that transfer directly:

- source: bit25 HW84
- target lane: bit13 HW82 lane
- objective: `HW + 2 * lane_L1`
- pair rank: same target objective
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- max pairs/radius: 6/12

Result:

- best seen HW: 84, source init
- best target objective: init, objective 104
- no lower-HW records
- no better target-lane state than the start
- wall: 719.56s

Interpretation:

The bit25-to-bit13 lane transfer is closed at the standard M2 pair-beam scale.
Lane proximity alone is not enough; the operator cannot cheaply move the bit25
absorber into the bit13 shape. This supports treating the current portfolio as
several distinct shelves rather than one shared lane basin.
