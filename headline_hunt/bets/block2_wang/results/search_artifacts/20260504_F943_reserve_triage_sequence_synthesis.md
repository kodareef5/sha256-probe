# Reserve Triage Sequence Synthesis

This sequence tested fresh F905 reserve-triage rows with the calibrated
shape-reserve beam, then deepened the two interesting hits.

| run | source | init | best | verdict | key signal |
| --- | --- | ---: | ---: | --- | --- |
| F906 | F788 top_by_hw[1] | 86 | 86 | closed | only HW89 mixed; final low-net HW93 |
| F911 | F788 top_by_hw[2] | 87 | 87 | closed | final HW90 add7/remove5/net+2 |
| F915 | F788 top_by_hw[3] | 87 | 87 | closed | best mixed HW91 |
| F919 | F793 top_by_hw[1] | 88 | 88 | closed | best mixed HW90; final low-net HW95 |
| F923 | F788 top_by_hw[4] | 88 | 87 | pass | final mixed HW87 add7/remove5/net+2 |
| F927 | F923 HW87 deepen | 87 | 87 | closed | F923 was one-hop under this operator |
| F931 | F799 top_by_hw[1] | 88 | 88 | closed | best mixed HW89 |
| F935 | F788 top_by_hw[5] | 88 | 83 | weak | strong pure-add HW83 add6/remove0/net+6 |
| F939 | F935 HW83 deepen | 83 | 83 | closed | pure-add HW83 is locally closed under plain reserve beam |

Takeaways:

- The calibrated mixed-low-net channel produced one fresh pass: F923, but its
  direct deepen closed at HW87.
- F935 produced the best raw record in this sequence, HW83, but it came from a
  pure-add depth-3 state rather than the mixed channel.
- The plain reserve beam is good at classifying one-hop repair coverability,
  but it is not enough to deepen either F923 HW87 or F935 HW83.
- The next useful compute should not be another identical deepen. It should
  alter the local objective around the F935 HW83 state, favoring removal and
  low net-add moves to test whether the pure-add spike can be converted into a
  repair basin.

Recommended next run:

- Start from F935 best_seen HW83.
- Add objective pressure against net additions and for removals.
- Keep reserve slots, but make the low-net reserve stricter so the beam spends
  more capacity on repair-shaped moves.

