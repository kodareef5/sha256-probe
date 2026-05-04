# F826 Mac Absorber Shape Note

Mac's new F550/F551 absorber results were checked with the F818 transition-cover
analyzer.

## F550 Bit24 F428-Basis HW84

- Source/target HW: 131->84
- M2 weight: 44->54
- Transition bits: 10
- Top-pool covers: 1/945
- Cover shape: five add-add pairs
- Added/removed: added10/removed0

This is a large cross-basis absorber descent from a high-HW starting point. The
pure-add shape is not automatically bad in that context, but it is the same
shape family as the F799->F800 overfill repair.

## F551 Bit15 HW88

- Source/target HW: 139->88
- M2 weight: 0->8
- Transition bits: 8
- Top-pool covers: 1/105
- Cover shape: four add-add pairs
- Added/removed: added8/removed0

This is cold-start absorber construction, so pure additions are expected.

## Interpretation

The shape selector should distinguish two regimes:

- absorber construction from M2=0 or cross-basis mismatch: pure additions are
  normal and useful;
- repair from an already-good sparse detour: pure additions can signal an
  overfill trap.

F788 remains the model for the second regime: it repairs by a balanced
added8/removed4/net+4 transition and survives mild shape bias. F799 fails that
test because its only improving repair remains added10/removed0/net+10.
