# F828 F552/F553 Shape Interpretation

F827 extended the transition-cover check to Mac's newest absorber runs.

## F552 Bit15 HW88->HW83

- Source/target HW: 88->83
- M2 weight: 8->18
- Transition shape: added10/removed0/net+10
- Cover shape: five add-add pairs
- Top-pool covers: 1/945

Even though this starts from an already-good HW88 absorber, the source M2 is
still very light. This looks like absorber growth, not mature sparse repair.
Pure additions are still useful in this regime.

## F553 Bit18 Cold HW86

- Source/target HW: 113->86
- M2 weight: 0->8
- Transition shape: added8/removed0/net+8
- Cover shape: four add-add pairs
- Top-pool covers: 1/105

This matches the cold-start absorber pattern from F551.

## Updated Shape Rule

Use three regimes, not two:

- cold construction: M2 near 0, pure-add covers are expected;
- absorber growth: low M2 weight, pure-add covers can still be productive;
- mature repair: M2 already around 40+, pure-add covers are suspicious and can
  lead to overfilled closed basins.

F788/F789 is the mature-repair positive example. F799/F800 is the mature-repair
overfill negative example. F550/F551/F552/F553 are construction or growth
examples and should not be rejected for pure-add shape alone.
