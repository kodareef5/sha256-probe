# 20260517 Energy Bridge Notes

Current exact frontier remains the phase-234 joint anchor:

- exact joint: tail=11 r61=11, W1=0x3e31,0x0cdb,0x286a
- exact tail: tail=10 r61=12, W1=0x3384,0x0997,0x12b7
- exact r61: r61=9 tail=23, W1=0x121c,0x3035,0x3416

New local scan shapes from phases 324-331:

- phase324 window=3842: tail=13 r61=21, W1=0x3ba7,0x0d0d,0x338a
- phase324 window=3842: r61=13 tail=26, W1=0x14c1,0x3aa7,0x2393
- phase325 window=7954: tail=16 r61=16, W1=0x2d13,0x05b3,0x1b25
- phase331 window=882: tail=16 r61=17, W1=0x1a5d,0x3d95,0x1d08
- phase334 window=547: tail=13 r61=14, W1=0x160a,0x1400,0x3d93
- phase337 window=1363: tail=16 r61=16, W1=0x298f,0x3786,0x06aa
- phase338 window=6755: tail=15 r61=15, W1=0x0f24,0x3e0f,0x2b4d
- phase340 window=2820: tail=14 r61=16, W1=0x22c5,0x24ca,0x164c
- phase343 window=2100: tail=15 r61=18, W1=0x37b2,0x3648,0x2a2d
- phase346 window=3684: tail=18 r61=19, W1=0x0ab7,0x14c2,0x15ce
- phase346 window=4452: r61=11 tail=29, W1=0x0c4a,0x3a50,0x0e9d
- phase347 window=5236: tail=17 r61=15, W1=0x11aa,0x233f,0x0595
- phase347 window=1140: r61=11 tail=31, W1=0x11ac,0x22e8,0x1b8a
- phase349 window=7445: tail=19 r61=17, W1=0x1d4c,0x1e37,0x2d7e
- phase349 window=7445: r61=10 tail=28, W1=0x061c,0x0522,0x2622
- phase350 window=1629: tail=17 r61=14, W1=0x1a07,0x079d,0x129a
- phase350 window=5781: tail=21 r61=11, W1=0x37de,0x0132,0x3a37
- phase351 window=3822: tail=16 r61=14, W1=0x1bf3,0x3294,0x21c7
- phase351 window=6726: r61=10 tail=27, W1=0x3d0a,0x1c32,0x04d9
- phase352 window=446: tail=17 r61=19, W1=0x206f,0x25c0,0x1acf
- phase353 window=4167: tail=16 r61=16, W1=0x1fb9,0x1bd0,0x3d14
- phase354 window=3173: tail=14 r61=16, W1=0x3c4a,0x0174,0x205b
- phase355 window=5398: r61=10 tail=33, W1=0x0661,0x3b7a,0x37c3
- phase357 window=534: tail=15 r61=18, W1=0x0e14,0x1274,0x1da6
- phase357 window=1046: tail=18 r61=10, W1=0x0b4d,0x0ac8,0x0286
- phase357 window=2070: repeat of global tail=10/r61=12 seed,
  W1=0x3384,0x0997,0x12b7
- phase358 window=806: tail=17 r61=12, W1=0x288b,0x3eb8,0x235b
- phase359 window=6454: tail=17 r61=13, W1=0x2e86,0x356b,0x29ac
- phase360 window=3142: tail=16 r61=19, W1=0x185e,0x01b4,0x1c91

The repeatable repaired nonzero bridge seed from 10M energy-prefix probes:

- repaired nonzero surrogate: tail=16 r61=16 d60=0x3ce1 d60_hw=8
- W1=0x3e31,0x0cbb,0x2e80
- W2=0x3d3e,0x12ba,0x0b91

The first 1B prefix2 bridge from that seed improved the repaired nonzero
surrogate without moving the exact frontier:

- repaired nonzero surrogate: energy=939 tail=13 r61=12 d60=0x1312 d60_hw=5
- gh60=0x4689daa
- W1=0x1e71,0x1459,0x1fb5
- W2=0x1d7e,0x16c4,0x19e4

The phase325 16/16 solo prefix2 lane found a closer repaired nonzero
bridge:

- repaired nonzero surrogate: energy=865 tail=11 r61=12 d60=0x0109 d60_hw=3
- gh60=0x448c59a
- W1=0x04aa,0x1053,0x2db5
- W2=0x03b7,0x3e07,0x2150

The 939 bridge lane found a nearby but weaker repaired nonzero point:

- repaired nonzero surrogate: energy=872 tail=11 r61=12 d60=0x1fe9 d60_hw=10
- gh60=0x4617cee
- W1=0x2f10,0x2f5b,0x065a
- W2=0x2e1d,0x08bf,0x36bf

The 865 solo and bridge repeats preserved the same best nonzero surrogate
without improving it.

The phase333, phase334, phase336, and phase337 bridge follow-ups also
preserved the same best nonzero surrogate without improving it:

- `20260517_phase333_tail16r14_nonzero865_bridge_energy_prefix2_1b.log`
- `20260517_phase334_tail13r14_nonzero865_bridge_energy_prefix2_1b.log`
- `20260517_phase337_tail16r16_nonzero865_bridge_energy_prefix2_1b.log`
- `20260517_phase336_tail16r13_nonzero865_bridge_energy_prefix2_1b.log`

The phase338 tail15/r15 bridge preserved the 865 repaired nonzero surrogate.
The phase338 solo lane found a distinct but weaker nonzero point:

- repaired nonzero surrogate: energy=938 tail=13 r61=10 d60=0x02f7 d60_hw=8
- gh60=0x5887ca6
- W1=0x0f2c,0x1e8e,0x3d42
- W2=0x0e39,0x1d29,0x21e0

The phase340 tail14/r16 bridge preserved the 865 repaired nonzero surrogate.
The phase340 solo lane found a closer but still weaker local point:

- repaired nonzero surrogate: energy=873 tail=12 r61=12 d60=0x1eae d60_hw=9
- gh60=0xd51859a
- W1=0x22c5,0x14ce,0x329b
- W2=0x21d2,0x0137,0x0a3f

The phase343 tail15/r18 bridge preserved the 865 repaired nonzero surrogate.
The phase343 solo lane found a weaker local point:

- repaired nonzero surrogate: energy=943 tail=12 r61=13 d60=0x3e8d d60_hw=9
- gh60=0xc889baa
- W1=0x21b1,0x226c,0x0e99
- W2=0x20be,0x1b83,0x38a1

The phase346/347 r61=11 bridge preserved the 865 repaired nonzero surrogate.
The phase347 tail17/r15 solo lane found a weaker local point:

- repaired nonzero surrogate: energy=1007 tail=11 r61=14 d60=0x0ac2 d60_hw=5
- gh60=0xde084e6
- W1=0x131b,0x2323,0x2ff0
- W2=0x1228,0x13e4,0x055f

The phase349 r61=10 solo lane found a local nonzero point that is closer
than phase340 but still behind the 865 bridge:

- repaired nonzero surrogate: energy=869 tail=12 r61=12 d60=0x0724 d60_hw=5
- gh60=0x460bfee
- W1=0x0f9f,0x05f0,0x3dd9
- W2=0x0eac,0x27ab,0x117d

The phase349 bridge preserved the 865 repaired nonzero surrogate and the
exact phase-234 frontier.

The phase350, phase351, and phase354 bridge lanes also preserved the 865
repaired nonzero surrogate and the exact phase-234 frontier. The phase354
solo lane found a weaker local point:

- repaired nonzero surrogate: energy=942 tail=13 r61=13 d60=0x0d91 d60_hw=6
- gh60=0x5a05dfa
- W1=0x3e9a,0x25fe,0x3295
- W2=0x3da7,0x16d2,0x254c

Refresh6 exact-refinement plan:

- `20260517_joint_first_refresh6_top384.txt`
- 49,280 registry entries, 772 candidate seeds, 193 batches
- batches 0-4 completed with the exact frontier unchanged
- refresh5 batches 24-25, refresh5b batch 42, and refresh6 batch 6 also
  completed with the exact frontier unchanged
- refresh5 batches 26-27, refresh5b batch 43, and refresh6 batch 7 also
  completed with the exact frontier unchanged
- active first lane: batches 0-31 with 16-seed crossover expansion

Active follow-up lanes:

- breadth scan phases 356-363, start windows 6,22,...,118
- refresh5 gap queue: batches 24-31 and 42-63
- refresh6 xover queue: batches 6-31
- phase357 tail18/r61=10 solo, W1=0x0b4d,0x0ac8,0x0286
- phase357 bridge with 865, 873, and 869 nonzero seeds
- phase360 tail16/r61=19 solo, W1=0x185e,0x01b4,0x1c91
- phase358/359 mixed bridge with 865 and 873 nonzero seeds
