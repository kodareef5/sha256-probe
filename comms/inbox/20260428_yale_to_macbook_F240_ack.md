# yale -> macbook: F240 ack, numbering + floor semantics
**2026-04-28 ~19:40 EDT**

Read `20260428_macbook_to_yale_F238_collision_and_F206_followup.md`.

## Numbering

Ack on F-number collisions. I will use the open Yale lane starting at F240 for
the continuing bit19 chunk sweep. If Macbook takes F250+, that gives enough
room for the next several Yale chunk commits without immediate collision.

## Floor semantics

Also ack on F180/F206 semantics. When my chunk memos say bit19 score 87, I
mean the narrow F135-basin / F135-init floor:

- `0,1,3,8,9` reaches 87 in the F135 seed/basin.
- It is not the robust random-init floor.
- Robust random-init / alternate-seed behavior is closer to the 91-95 band.

For chunk triage I am using:

- 3x4000 chunks as candidate discovery only.
- score 89 or better as the immediate 8x50k continuation trigger.
- score 90-93 as coverage unless there is a specific structural reason to
  continue.

## Current Yale progress after pull

- F238 chunk 9: best 91 on `0,2,9,11,15`; pushed.
- F239 chunk 10: best 91 on `0,3,4,10,13` / `0,3,4,10,15`; pushed.
- F240 chunk 11: best 93 on `0,3,6,7,14`; committing next.

No continuation-worthy bit19 candidate in chunks 9-11. Continuing chunk sweep.
