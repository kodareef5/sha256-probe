# 2026-05-17: Free-Word Shaping MITM Reduced-N Pilot

Runner: mac-codex

## Question

Can the remaining free words be shaped and then met in the middle at the W60
schedule interface?

For the cascade-shaped sr=61 model, define:

```text
D60 = W2_sched60 - W2_required60  mod 2^N
```

where:

- `W2_sched60` is forced by the message schedule from W58.
- `W2_required60` is the word needed to start the e-register zeroing cascade.
- `D60=0` is the first sr=61 interface match.

## Artifact

New prototype:

```text
headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c
```

Compile:

```bash
gcc -O3 -march=native -o /private/tmp/free_word_mitm_reducedn \
  headline_hunt/bets/mitm_residue/prototypes/free_word_mitm_reducedn.c -lm
```

## Results

### N=8 exact

```text
prefixes=65536/65536 mode=exact
total triples=16777216
D60=0 matches=65954
random expectation=65536.0
enrichment=1.006x
prefixes with D60=0=38505
max D60=0 fiber per prefix=10 at W57=0x6 W58=0x58
final tail collisions=0
best r61 HW=5
best tail HW=9
```

### N=10 exact

```text
prefixes=1048576/1048576 mode=exact
total triples=1073741824
D60=0 matches=1045126
random expectation=1048576.0
enrichment=0.997x
prefixes with D60=0=410095
max D60=0 fiber per prefix=32 at W57=0xae W58=0xd4
final tail collisions=0
best r61 HW=6
best tail HW=7
```

### N=12 sampled

```text
prefixes=65536/16777216 mode=permuted-prefix-sample
total triples=268435456
D60=0 matches=65266
random expectation=65536.0
enrichment=0.996x
prefixes with D60=0=32366
max D60=0 fiber per prefix=19 at W57=0x484 W58=0x4ea
final tail collisions=0
best r61 HW=10
best tail HW=15
```

## Interpretation

`D60=0` is reachable and abundant, but it is not enriched relative to a random
N-bit interface. In this cascade-shaped model, the W60 schedule match by itself
is not the hard miracle and not enough to close the tail.

This changes the MITM key design:

```text
bad key:  D60 only
next key: D60 + r61 residual bucket + tail carry chamber signature
```

The exact N=8/N=10 passes found no full tail collisions among `D60=0` matches.
The best exact N=10 tail residual is HW7, so there is still structured signal,
but it lives after the W60 interface.

## Next step

Extend the prototype to record a keyed table over:

- `D60`,
- r61 residual active-bit set,
- `(g60,h60)` hard residue,
- round 60..63 carry chamber signature.

Then rerun N=8/N=10 and ask whether the enhanced key creates fat buckets that
predict low final tail HW. If it does not, the simple free-word MITM route is
diagnostic only, not a construction path.
