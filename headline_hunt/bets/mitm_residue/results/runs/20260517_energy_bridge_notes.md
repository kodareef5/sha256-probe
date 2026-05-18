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
- phase361 window=854: tail=16 r61=16, W1=0x2061,0x2954,0x3344
- phase362 window=870: tail=18 r61=12, W1=0x243d,0x13a0,0x2b58
- phase363 window=2422: tail=18 r61=18, W1=0x1326,0x0792,0x13f2
- phase364 window=3847: tail=16 r61=23, W1=0x2ff5,0x005d,0x166f
- phase365 window=6679: tail=18 r61=16, W1=0x0833,0x1d78,0x3640
- phase366 window=2855: tail=17 r61=13, W1=0x10cc,0x03d5,0x3b24
- phase367 window=6455: tail=16 r61=18, W1=0x15c2,0x373d,0x3da7
- phase367 window=6711: r61=11 tail=26, W1=0x075a,0x16f7,0x0b80
- phase368 window=7751: tail=18 r61=13, W1=0x3bd5,0x3953,0x2f00
- phase368 window=583: r61=11 tail=27, W1=0x33e0,0x2bb3,0x3070
- phase369 window=4439: tail=19 r61=14, W1=0x0639,0x1456,0x33c8
- phase370 window=2663: tail=18 r61=18, W1=0x38e9,0x0037,0x3c54
- phase370 window=871: r61=11 tail=29, W1=0x3bcf,0x25d7,0x2178
- phase371 window=2935: tail=16 r61=22, W1=0x3186,0x2eb7,0x0baf
- phase371 window=3703: r61=11 tail=31, W1=0x19dc,0x2f90,0x122a

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

The phase357 tail18/r61=10 solo lane found a nonzero surrogate with a very
low tail but weaker scalar energy than the 865 bridge:

- repaired nonzero surrogate: energy=928 tail=7 r61=13 d60=0x0360 d60_hw=4
- gh60=0x49887aa
- W1=0x036d,0x0be3,0x18d1
- W2=0x027a,0x3ca7,0x3a64

The phase357 bridge and phase358/359 bridge lanes preserved the 865 repaired
nonzero surrogate. The phase360 tail16/r61=19 solo lane found a weaker local
point:

- repaired nonzero surrogate: energy=936 tail=13 r61=10 d60=0x0395 d60_hw=6
- gh60=0x4a047e6
- W1=0x1b8c,0x2364,0x0fe1
- W2=0x1a99,0x1d34,0x1880

The phase357 nonzero928 solo follow-up produced the new repaired nonzero
energy frontier:

- repaired nonzero surrogate: energy=802 tail=11 r61=11 d60=0x37da d60_hw=10
- gh60=0xc904766
- W1=0x2bcc,0x01c6,0x0dab
- W2=0x2ad9,0x2e0a,0x1f4e

The phase357 nonzero928 energy-walk preserved the older 865 bridge, and the
phase361 solo lane found a close but weaker point:

- repaired nonzero surrogate: energy=867 tail=11 r61=12 d60=0x282a d60_hw=5
- gh60=0x4a08cea
- W1=0x1921,0x3d57,0x2686
- W2=0x182e,0x11fe,0x0098

The phase357/361/364 bridge preserved the 865 nonzero point, but also
reconfirmed the exact phase-234 joint anchor as a repaired energy surrogate
with energy=792 and d60=0; that exact witness does not supersede the nonzero
frontier.

The phase357 nonzero802 bridge improved the repaired nonzero frontier from
802 to 798:

- repaired nonzero surrogate: energy=798 tail=11 r61=10 d60=0x2b99 d60_hw=8
- gh60=0x490876a
- W1=0x235d,0x1ef3,0x1368
- W2=0x226a,0x1639,0x141f

The phase357 nonzero802 energy-walk then produced a much stronger repaired
nonzero frontier:

- repaired nonzero surrogate: energy=652 tail=8 r61=9 d60=0x3126 d60_hw=6
- gh60=0x4908f6a
- W1=0x075d,0x24ea,0x2ccc
- W2=0x066a,0x0ff9,0x2bd3

Refresh6 exact-refinement plan:

- `20260517_joint_first_refresh6_top384.txt`
- 49,280 registry entries, 772 candidate seeds, 193 batches
- batches 0-4 completed with the exact frontier unchanged
- refresh5 batches 24-25, refresh5b batch 42, and refresh6 batch 6 also
  completed with the exact frontier unchanged
- refresh5 batches 26-27, refresh5b batch 43, and refresh6 batch 7 also
  completed with the exact frontier unchanged
- refresh5 batches 28-29, refresh5b batch 44, and refresh6 batch 8 also
  completed with the exact frontier unchanged
- active first lane: batches 0-31 with 16-seed crossover expansion
- refresh5 batches 30-31, refresh5b batches 45-46, refresh5c batches 64-65,
  and refresh6 xover batches 9-10 also completed with the exact frontier
  unchanged
- refresh5b batch 47, refresh5c batches 66-67, and refresh6 xover batch 11
  also completed with the exact frontier unchanged
- refresh5b batch 48, refresh5c batches 68-69, and refresh6 xover batch 12
  also completed with the exact frontier unchanged
- refresh5b batches 49-63, refresh5c batches 70-95, and refresh6 xover
  batches 13-31 also completed with the exact frontier unchanged

Refresh7 exact-refinement plan:

- `20260517_joint_first_refresh7_top640.txt`
- 76,800 registry entries, 321 batches
- global seeds include exact tail, exact r61, exact joint, phase334, nonzero802,
  and new nonzero652
- active lanes: refresh7a batches 0-63 and refresh7b batches 64-127

Phase372 breadth highlights from the start-window-8 band:

- phase372 window=7176: tail=13 r61=18, gh60=0x7ba5ca6,
  W1=0x00f4,0x0ddd,0x285e, W2=0x0001,0x160c,0x3600
- phase372 window=3592: tail=14 r61=14, gh60=0x4a3ccfe,
  W1=0x3918,0x1174,0x2094, W2=0x3825,0x29dc,0x24a9
- phase372 window=1544: tail=19 r61=10 self-aligned, gh60=0xc885b9a,
  W1=0x1daa,0x3bd0,0x07f6, W2=0x1cb7,0x2d19,0x0f1a

Phase373 breadth highlights from the start-window-24 band:

- phase373 window=5656: tail=19 r61=17, gh60=0x7d69c9a,
  W1=0x2049,0x15cf,0x24cb, W2=0x1f56,0x369b,0x2fa6
- phase373 window=5656: r61=11 tail=25, gh60=0x4a885aa,
  W1=0x027d,0x0e12,0x3845, W2=0x018a,0x19a6,0x1d5b
- phase373 window=6168: r61=11 tail=31, gh60=0xc70856e,
  W1=0x2c4f,0x26e9,0x10c1, W2=0x2b5c,0x0b37,0x1d67

Phase374-379 breadth highlights from the remaining start-window-40..120 band:

- phase374 window=2856: tail=17 r61=17,
  W1=0x2169,0x2e5c,0x278d, W2=0x2076,0x2bf0,0x0167
- phase374 window=5416: r61=11 tail=22,
  W1=0x1761,0x3221,0x0a95, W2=0x166e,0x0230,0x20e5
- phase375 window=568: tail=17 r61=17,
  W1=0x1271,0x20a0,0x0d6e, W2=0x117e,0x2e48,0x3d0d
- phase376 window=328: r61=11 tail=21,
  W1=0x16fc,0x190b,0x033c, W2=0x1609,0x3618,0x22c2
- phase377 window=856: r61=11 tail=19,
  W1=0x239b,0x38f5,0x2081, W2=0x22a8,0x2132,0x1288
- phase378 window=5480: r61=11 tail=18,
  W1=0x3f71,0x20ed,0x365b, W2=0x3e7e,0x2178,0x38e8
- phase379 window=3704: tail=19 r61=16,
  W1=0x24e9,0x3b40,0x3c4e, W2=0x23f6,0x2193,0x251e

Phase380 breadth highlights from the next start-window-9 band:

- phase380 window=2825: tail=17 r61=20,
  W1=0x2949,0x0d15,0x0888, W2=0x2856,0x2e23,0x1a51
- phase380 window=1801: tail=18 r61=12 balanced,
  W1=0x2bae,0x03b4,0x1e39, W2=0x2abb,0x03fd,0x2ad8
- phase380 window=7945: tail=18 r61=19,
  W1=0x0bd0,0x3711,0x0198, W2=0x0add,0x2950,0x335a

Active follow-up lanes:

- breadth scan phases 388-395, start windows 10,26,...,122; phase388 active
- refresh7 queues: batches 0-63 and 64-127
- 5B nonzero652 solo, energy-walk, phase372-379 bridge, and phase380 bridge
