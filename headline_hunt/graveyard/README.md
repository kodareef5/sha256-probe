# Graveyard

Closed bets and their kill memos. Once a bet's kill criteria fire, it gets:

1. Status flipped to `closed` in `registry/mechanisms.yaml`.
2. Bet directory moved to `graveyard/closed_bets/<bet_id>/`.
3. A kill memo written: `graveyard/closed_bets/<bet_id>/KILL_MEMO.md`,
   following `KILL_MEMO_TEMPLATE.md`.
4. Reopen criteria preserved in the mechanism entry.

**Why this exists**: prevents reanimation. A future agent (or future you)
who proposes redoing a closed bet must first read the kill memo and meet
its reopen criteria. No silent restarts.
