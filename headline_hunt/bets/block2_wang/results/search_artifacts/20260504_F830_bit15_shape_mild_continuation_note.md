# F830 Bit15 Shape-Mild Continuation Note

F829 continued Mac's F552 bit15 HW83 absorber with the calibrated mild shape
bias:

- init HW: 83
- init lane: `[10, 6, 12, 14, 13, 6, 12, 10]`
- init M2 weight: 18
- objective/pair-rank: cg/cg
- shape bias: net-add penalty `0.5`, removed-bit bonus `0.25`
- max pairs/radius: 6/12

Result:

- best seen HW: 83, source init
- new records: 0
- depth best HW sequence: 92, 92, 89, 90, 92, 90
- wall: 831.48s

Interpretation:

F552's HW83 record is closed under this mild shape-aware cg continuation. That
does not prove bit15 is exhausted, but it says the next improvement probably
needs either a plain add-heavy growth step, a different objective, or a wider
beam/radius. This is a useful comparator for Mac's planned F554/F555 plain cg
continuations.
