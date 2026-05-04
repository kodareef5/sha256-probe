# F861 bit25 -> bit13 Pair Gate Note

F843 and F845 closed bit25 HW84 -> bit13 HW82 under target-lane beam
objectives. F860 adds the missing local pair-potential denominator.

Setup:

- source: bit25 HW84
- source lane: `[9, 11, 13, 10, 9, 9, 9, 14]`
- target: bit13 HW82 lane `[10, 11, 9, 12, 9, 7, 10, 14]`
- initial target L1: 10
- source M2 weight: 28

F860 all-pair result:

- total pairs: 130,816
- HW-improving pairs: 0
- HW-nonworse pairs: 0
- c/g-improving pairs: 1
- target-L1-improving pairs: 0
- best HW pair: HW92
- best target pair: L1 15 at HW97

Verdict:

The closest-lane portfolio transfer has no local target-lane gradient. The
failure is stronger than "the beam could not compose the right moves"; the
one-pair neighborhood already points away from the bit13 lane.
