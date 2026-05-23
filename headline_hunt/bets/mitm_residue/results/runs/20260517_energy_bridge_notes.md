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
- note: refresh7 is a mixed exact/nonzero bridge queue; summaries dominated by
  W1=0x075d,0x24ea,0x2ccc should be interpreted as nonzero-energy bridge
  behavior, not exact frontier movement

Refresh8 exact-only refinement plan:

- `20260517_joint_first_refresh8_exactonly_top640.txt`
- 87,040 registry entries, 216 batches
- global seeds restricted to exact tail, exact r61, exact joint, and phase334
- active first lane: batches 0-31 with nonzero802/nonzero652 excluded

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

Phase388 breadth highlights from the start-window-10 band:

- phase388 window=2570: tail=17 r61=18,
  W1=0x01d5,0x1c6c,0x1c28, W2=0x00e2,0x0ca7,0x33bc
- phase388 window=3338: tail=17 r61=19,
  W1=0x083f,0x2ef8,0x1bd8, W2=0x074c,0x1847,0x050e
- phase388 window=4618: tail=18 r61=14 and best_r61=10 in same window,
  tail W1=0x2f7d,0x2e33,0x179b, r61 W1=0x330d,0x04c1,0x2213

Phase389 breadth highlights from the start-window-26 band:

- phase389 window=3098: tail=15 r61=16, gh60=0x4ab44ba,
  W1=0x39f6,0x3130,0x395c, W2=0x3903,0x266f,0x2ec5
- phase389 window=7450: tail=18 r61=17 with a separate r61=12 witness,
  tail W1=0x3c73,0x2d3d,0x3cc1, r61 W1=0x0ba5,0x1c5a,0x1b10
- phase389 window=26: r61=12 tail=26,
  W1=0x0eab,0x0ba3,0x3727, W2=0x0db8,0x125d,0x2578

Phase390 breadth highlights from the start-window-42 band:

- phase390 window=4394: tail=17 r61=17, gh60=0xc6045fa,
  W1=0x1c9a,0x3041,0x3fed, W2=0x1ba7,0x2dd6,0x132c
- same phase390 window also has a separate r61=12 tail=26 witness,
  W1=0x334f,0x0326,0x1b79, W2=0x325c,0x1068,0x30a8

Phase391-395 breadth highlights from the completed start-window-58..122 band:

- phase391 window=6970: self-aligned tail=18 r61=10,
  W1=0x2ca2,0x3c60,0x21fb, W2=0x2baf,0x0d97,0x19ca
- phase393 window=2650: tail=17 r61=17 with a separate r61=10 witness,
  tail W1=0x3f2f,0x1991,0x3f96, r61 W1=0x080a,0x1674,0x07ea
- phase394 window=3434: tail=14 r61=18,
  W1=0x00c9,0x1a5b,0x25c6, W2=0x3fd6,0x30ff,0x307c
- phase394 window=362: tail=15 r61=21 with a separate r61=12 witness,
  tail W1=0x0835,0x2095,0x3f35, r61 W1=0x3e8f,0x053c,0x1565
- phase395 window=122: tail=16 r61=19 with a separate r61=11 witness,
  tail W1=0x2f8e,0x0b51,0x114d, r61 W1=0x32bb,0x2f1d,0x285c

Completed 5B nonzero652 bridge lanes:

- solo prefix2, energy-walk, phase372-379 bridge, phase380 bridge, and
  phase388 bridge all completed without beating the repaired nonzero energy
  frontier of 652
- phase380 and phase388 bridges did expose a raw repaired tail=7 r61=13 point
  at W1=0x036d,0x0be3,0x18d1, W2=0x027a,0x3ca7,0x3a64, but the best
  nonzero energy/joint witness remains W1=0x075d,0x24ea,0x2ccc

Completed refinement queues:

- refresh7 mixed exact/nonzero queues completed batches 0-127; summaries were
  dominated by the nonzero652 anchor and did not move the exact frontier
- refresh8 exact-only queue completed batches 0-31; exact frontier unchanged
- next exact-only queue segment should continue at refresh8 batch 32

Active follow-up lanes:

- no active lanes as of the May 23 restart check
- next breadth band: phases 396-403, start windows 11,27,...,123
- next exact-only lane: refresh8 batches 32-95
- next nonzero bridge lane: nonzero652 plus phase394/393/391/389 seeds

May 23 continuation checkpoint:

- committed the prior restart work at 3350e7c2; remaining dirty paths were
  unrelated workspace changes and were left alone
- rebuilt the /private/tmp reduced-n binaries and restarted refresh8 exact-only
  batches 32-95, including a retry for batch 32 after the first missing-binary
  launch created an empty log
- refresh8 exact-only batches 32-48 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 396-403 completed without a frontier move; notable rows were:
  phase400 tail17/r6111 at window 4683,
  phase401 tail19/r6110 at window 7003, and
  phase403 tail17/r6114 at window 4731
- breadth phases 404-411 completed without an exact improvement, but produced
  several bridge-worthy seeds:
  phase404 window 6924 reached equal-frontier r61=9 with joint tail19/r619
  and a separate r61 row at tail25;
  phase407 window 1340 reached tail16/r6116;
  phase408 window 1868 reached tail16/r6116;
  phase409 window 6748 reached tail18/r6110;
  phase410 windows 2412 and 4716 reached tail16;
  phase411 window 1916 reached tail17/r6112
- launched a new phase404/phase401/phase400 targeted energy bridge lane with
  nonce 835402 in addition to the older phase394/393/391 and tail7/r6110
  bridge lanes; all three energy lanes were still running at this checkpoint
- breadth scanning continued into phases 412-419 with start windows
  13,29,45,61,77,93,109,125

May 23 continuation checkpoint 2:

- amended the previous checkpoint metadata so both author and committer are
  kodareef5 <kodareef5@users.noreply.github.com>; no file content changed in
  that amend
- refresh8 exact-only batches 49-57 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 412-419 completed without a tail<=13 or r61<=8 move; notable
  bridge rows were:
  phase412 window 781 tail15/r6115 and window 2829 tail15/r6113;
  phase417 window 7517 tail16/r6112 plus a separate r61=11 row at window 4957;
  phase419 window 7549 tail16/r6120 plus a separate r61=11 row at window 3197
- phase414-416 were ordinary breadth coverage, with best tail17/18 and
  best_r61=11; phase418 topped out at tail18/r6112
- the phase394/393/391/nonzero652 and tail7/r6110 5B energy bridge lanes
  completed without beating the repaired nonzero energy frontier of 652; the
  tail7/r6113 witness remains a tail outlier, not an energy improvement
- launched two follow-up 5B energy bridge lanes from the phase417/418 tail16-18
  cluster and the phase415-419 r61=11/12 cluster; both were still running at
  this checkpoint
- breadth scanning continued into phases 420-427 with start windows
  14,30,46,62,78,94,110,126

May 23 continuation checkpoint 3:

- refresh8 exact-only batches 58-68 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 420-427 completed without a tail<=13 or r61<9 move; the
  main new candidate was phase421 window 3358 with an equal-frontier r61=9
  witness, W1=0x3c3d,0x1862,0x1ee8 and W2=0x3b4a,0x2e8e,0x0077; its joint
  row was tail19/r6117 at W1=0x23b3,0x3aca,0x3a15
- other bridge-worthy low-tail rows in this tranche were phase420 tail16 at
  windows 14 and 1550, phase425 tail17 at window 2398, phase426 tail17 at
  window 3950, and phase427 tail16 at window 5246
- the phase404/401/400 and phase412-tail15 energy bridge lanes completed
  without beating the repaired nonzero energy frontier of 652
- launched two follow-up 5B energy bridge lanes with nonce 835406 and 835407:
  one mixes phase421 r61=9 with low-tail rows from phases 420-427, and the
  other stacks new r61=9/10/11 witnesses from phases 420-425
- breadth scanning continued into phases 428-435 with start windows
  15,31,47,63,79,95,111,127

May 23 continuation checkpoint 4:

- committed checkpoint 3 as 348f0cde with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 69-76 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 428-435 completed without a tail<=13 or r61<9 move; the best
  rows were phase428 r61=10 at window 5135, phase431 tail16 at window 6719,
  phase432 tail17 at windows 3919 and 6223, phase433 tail17 at window 2143,
  and phase435 tail17 at window 4223
- phase429, phase430, and phase434 were ordinary breadth coverage; their best
  tails were 18, 20, and 18, and their best_r61 values were 11, 11, and 12
- the four active 5B energy bridge lanes from checkpoint 2/3 were still
  running at this checkpoint
- breadth scanning continued into phases 436-443 with start windows
  16,32,48,64,80,96,112,128

May 23 continuation checkpoint 5:

- committed checkpoint 4 as 57956b79 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 77-86 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 436-443 completed without a tail<=13 or r61<=8 move; the
  best new bridge rows were phase439 window 832 tail15/r6121,
  phase437 window 4896 tail16/r6115, phase440 window 6992 tail16/r6113,
  phase442 window 1648 tail16/r6114 with a separate r61=11 row, and phase443
  windows 5760 and 7808 at tail17
- the lowest r61 rows in this tranche were phase436 window 2064 at r61=10,
  phase439 windows 64 and 7744 at r61=10, and r61=11 rows in phases 437,
  440, 441, 442, and 443; none beat the r61=9 exact frontier
- the phase417/418 tail16-18 and phase415-418 r61=11/12 5B energy bridge
  lanes completed without beating the repaired nonzero energy frontier of 652
- the phase421 low-tail/r61 and phase436/437 bridge energy lanes were still
  running at this checkpoint
- breadth scanning continued into phases 444-451 with start windows
  17,33,49,65,81,97,113,129

May 23 continuation checkpoint 6:

- committed checkpoint 5 as 1fb347b3 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 87-95 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 444-451 completed without a tail<=13 or r61<=8 move; the
  strongest new row was phase450 window 3953 at tail14/r6117, W1=0x2b13,
  0x3500,0x1bfa and W2=0x2a20,0x33e1,0x12ee
- other useful low-tail rows in this tranche were phase445 window 7713
  tail15/r6119, phase444 window 2065 tail16/r6116, phase446 window 1073
  tail17/r6119, phase449 window 1377 tail17/r6121, and phase451 window 3713
  tail17/r6116
- the best r61 rows in the tranche stayed at r61=11 or worse, with phase444
  window 17, phase445 window 5153, phase446 windows 6961/6449, phase448
  windows 1105/4689, phase449 window 3681, and phase450 windows 1905/1393
  all failing to approach the r61=9 exact frontier
- the phase421 r61=9/low-tail and phase420-425 r61=9/10/11 5B energy bridge
  lanes completed without beating the repaired nonzero energy frontier of 652
- launched three follow-up 5B energy lanes: phase445/444 low-tail mix
  nonce 835410, phase444-446 r61 bridge nonce 835411, and a dedicated
  phase450-tail14 low-tail bridge nonce 835412
- exact refresh8 scanning continued into batches 96-159, and breadth scanning
  continued into phases 452-459 with start windows 18,34,50,66,82,98,114,130

May 23 continuation checkpoint 7:

- committed checkpoint 6 as 8b6a6ea3 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 96-101 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 452-459 completed without a tail<=13 or r61<=8 move; notable
  low-tail rows were phase452 window 7954 tail16/r6116, phase454 window 1842
  tail16/r6118, phase458 window 882 tail16/r6117, and phase459 windows 3714
  and 7810 at tail17
- the best r61 row in this tranche was phase457 window 5730 at r61=10,
  W1=0x2b21,0x01c0,0x37c4 and W2=0x2a2e,0x09ea,0x1675; phase458 and phase459
  only reached r61=11
- the phase436/437 low-tail and r61 5B energy bridge lanes completed without
  beating the repaired nonzero energy frontier of 652
- launched two follow-up 5B energy lanes: phase457 r61=10 with phase452/454
  r61 rows and the phase450-tail14 seed at nonce 835413, and a mixed
  phase458/452/454 low-tail plus r61 bridge at nonce 835414
- exact refresh8 scanning continued into batches 102-159, and breadth scanning
  continued into phases 460-467 with start windows 19,35,51,67,83,99,115,131

May 23 continuation checkpoint 8:

- committed checkpoint 7 as 56c67d03 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 102-109 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 460-467 completed without an r61<=8 move; the strongest new
  low-tail row was phase461 window 547 at tail13/r6114, W1=0x160a,0x1400,
  0x3d93 and W2=0x1517,0x0bc3,0x1f5e
- the best r61 row in this tranche tied the existing r61=9 frontier at
  phase462 window 3891, W1=0x0c8b,0x13b6,0x2011 and W2=0x0b98,0x0671,
  0x273c; phase467 added two r61=11 rows, and phases460, 461, 463, and 465
  also produced r61=11 rows
- other useful low-tail seeds were phase465 window 6755 tail15/r6115,
  phase460 window 3859 tail16/r6114, phase463 window 7747 tail16/r6113,
  phase464 windows 1363 and 5203 tail16, and phase466/467 tail17 rows
- the phase445/444 low-tail and phase444-446 r61 5B energy bridge lanes
  completed without beating the repaired nonzero energy frontier of 652
- launched three follow-up 5B energy lanes: a dedicated phase461-tail13 bridge
  at nonce 835415, a phase462/467 r61 bridge at nonce 835416, and a mixed
  phase461/465/464/466 low-tail bridge at nonce 835417
- exact refresh8 scanning continued into batches 110-159, and breadth scanning
  continued into phases 468-475 with start windows 20,36,52,68,84,100,116,132

May 23 continuation checkpoint 9:

- committed checkpoint 8 as e584d1c0 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 110-121 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 468-475 completed without a tail<=13 or r61<=8 move; the
  strongest low-tail rows were phase470 window 2100 tail15/r6118,
  phase469 window 1316 tail16/r6122, phase474 window 5236 tail17/r6115,
  and phase475 window 2948 tail17/r6124
- the best r61 rows in this tranche were phase470 window 820 at r61=10,
  W1=0x3e9a,0x1c38,0x14ef and W2=0x3da7,0x0d0c,0x1b30, plus r61=11 rows
  in phases468, 469, 471, 473, 474, and 475
- the phase450-tail14 5B energy bridge lane completed without beating the
  repaired nonzero energy frontier of 652
- launched a phase470 tail15/r61=10 bridge at nonce 835418, seeded with the
  phase470 tail15 and r61=10 rows plus the phase461/450/462/457 anchors
- exact refresh8 scanning continued into batches 122-159, and breadth scanning
  continued into phases 476-483 with start windows 21,37,53,69,85,101,117,133

May 23 continuation checkpoint 10:

- committed checkpoint 9 as 279bb3fa with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 122-131 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 476-483 completed without a tail<=13 or r61<=8 move; the
  strongest new low-tail row was phase481 window 3173 at tail14/r6116,
  W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96
- other useful low-tail seeds were phase478 window 5685 tail16/r6114,
  phase480 window 2133 tail16/r6116, phase477 window 4133 tail17/r6114,
  phase479 window 6725 tail17/r6119, and phase483 window 1925 tail17/r6120
- the best r61 rows in this tranche were phase476 window 7445 r61=10,
  phase478 windows 7221 and 5429 at r61=10, phase481 window 357 at r61=10,
  and phase482 window 4725 at r61=10; phases477, 479, and 483 only reached
  r61=11
- the phase457/452/454, phase458/452/454, and phase461-tail13 5B energy
  bridge lanes completed without beating the repaired nonzero energy frontier
  of 652
- launched three follow-up 5B energy lanes: a phase478 tail16/r61=10 bridge
  at nonce 835419, a phase480/479/478 local bridge at nonce 835420, and a
  phase481 tail14/r61=10 bridge at nonce 835421
- exact refresh8 scanning continued into batches 132-159, and breadth scanning
  continued into phases 484-491 with start windows 149,165,181,197,213,229,
  245,261

May 23 continuation checkpoint 11:

- committed checkpoint 10 as 72ba2248 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 132-137 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 484-487 completed without a tail<=13 or r61<=8 move; the
  strongest new low-tail row was phase487 window 197 at tail15/r6116,
  W1=0x2f1a,0x0a34,0x3867 and W2=0x2e27,0x22f0,0x0047
- other useful low-tail rows were phase485 window 7333 tail17/r6118,
  phase487 window 4293 tail17/r6121, phase484 windows 1173 and 4757 at
  tail18, and phase486 windows 1461 and 4277 at tail19
- the best r61 rows in this tranche were phase485 window 2725 r61=10,
  W1=0x3a1f,0x39eb,0x15e9 and W2=0x392c,0x3701,0x2921, plus phase487
  window 5061 r61=10, W1=0x37d3,0x23af,0x0f3a and W2=0x36e0,0x12f5,
  0x1296; phase484 and phase486 only reached r61=11
- the phase462/467 and mixed phase461/465/464/466 5B energy bridge lanes
  completed without beating the repaired nonzero energy frontier of 652
- launched two follow-up 5B energy lanes from the phase485/481 low-tail and
  recent r61=10 spread at nonces 835422 and 835423
- exact refresh8 scanning continued into batches 138-159, and breadth scanning
  continued into phases 488-491

May 23 continuation checkpoint 12:

- committed checkpoint 11 as 8d31a864 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 138-141 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 488-491 completed without a tail<=13 or r61<=8 move; the
  strongest joint row was phase489 window 6629 at tail16/r6111,
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- other useful low-tail rows were phase490 window 6901 tail16/r6114,
  phase489 window 7653 tail17/r6116, phase488 window 7893 tail18/r6114,
  and phase491 window 3589 tail19/r6117
- the best r61 rows in this tranche were phase488 windows 7381, 725, 6613,
  and 4053 at r61=11, phase489 windows 6629 and 485 at r61=11, phase490
  window 7669 at r61=11, and phase491 window 6917 at r61=11
- the phase470-tail15/r61=10 5B energy bridge lane completed without beating
  the repaired nonzero energy frontier of 652
- launched follow-up 5B energy lanes for the phase487 tail15/r61=10 bridge
  at nonce 835424 and the phase489 tail16/r61=11 bridge at nonce 835425
- exact refresh8 scanning continued into batches 142-159, and breadth scanning
  continued into phases 492-499 with start windows 277,293,309,325,341,357,
  373,389

May 23 continuation checkpoint 13:

- committed checkpoint 12 as 84c87449 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 142-151 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 492-499 completed without a tail<=13 or r61<=8 move; phases
  492, 494, 497, and 498 rediscovered known r61=10 anchors, and phases 493,
  495, and 496 rediscovered known low-tail anchors
- the strongest low-tail row in the new phase499 window set was window 1925 at
  tail17/r6120, W1=0x03b9,0x3c8c,0x1b93 and W2=0x02c6,0x3d62,0x3643
- phase499 r61 rows bottomed at r61=11 in windows 3717, 4229, and 2181, with
  the best row W1=0x238b,0x1963,0x1933 and W2=0x2298,0x00ac,0x3bd2
- the phase478 tail16/r61=10 and phase480/479/478 local 5B energy bridge
  lanes completed without beating the repaired nonzero energy frontier of 652
- exact refresh8 scanning continued into batches 152-159, breadth scanning
  continued into phases 500-507 with start windows 405,421,437,453,469,485,
  501,517, and the phase481/485/487/489/recent-spread 5B energy lanes remain
  active
