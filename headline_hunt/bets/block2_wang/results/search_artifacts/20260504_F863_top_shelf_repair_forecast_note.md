# F863 Top-Shelf Repair Forecast Note

F862 ran the one-pair M2 repair forecast over the current top shelves:

- bit13 HW82
- bit15 HW83
- bit24/F428 HW84
- bit25 HW84
- bit14 HW85
- bit6 HW85

## Result

All six witnesses are one-pair closed:

| witness | base HW | M2 wt | best one-pair HW | improved pairs |
| --- | --- | --- | --- | --- |
| bit13 HW82 | 82 | 29 | 93 | 0/130816 |
| bit15 HW83 | 83 | 18 | 92 | 0/130816 |
| bit24/F428 HW84 | 84 | 54 | 95 | 0/130816 |
| bit25 HW84 | 84 | 28 | 92 | 0/130816 |
| bit14 HW85 | 85 | 12 | 94 | 0/130816 |
| bit6 HW85 | 85 | 18 | 93 | 0/130816 |

## Shape Read

The best local moves are mostly add-add:

- bit13: best HW is add2/remove0, HW93
- bit15: best HW is add2/remove0, HW92
- bit24/F428: best HW is add2/remove0, HW95
- bit25: best HW is add2/remove0, HW92
- bit14: best HW is add2/remove0, HW94
- bit6: tied best HW includes add1/remove1 and add2/remove0, both HW93

Removal-heavy local moves are worse across the board. This is consistent with
the construction/growth shelf picture: local additions can move the residual
around, but they do not open a mature balanced repair path.

## Practical Rule

Do not launch plain local pair beams from these six witnesses. The local
one-pair floor is 8-11 HW worse than each base, and no witness has an improving
pair. A next useful run needs a new upstream detour selector, not another local
continuation.
