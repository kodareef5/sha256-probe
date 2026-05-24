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

May 23 continuation checkpoint 14:

- committed checkpoint 13 as f33e83a2 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 152-159 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 500-507 completed without a tail<=13 or r61<=8 move; the
  strongest rows were rediscoveries of existing anchors rather than new
  frontiers
- phase501 rediscovered the phase485 tail17 row and r61=10 row; phase503
  rediscovered the phase487 tail15 and r61=10 rows; phase505 rediscovered the
  phase489 tail16/r6111 joint row; phase506 rediscovered the phase490 tail16
  row
- the remaining phases were weaker: phase500 bottomed at tail18/r61=11,
  phase502 at tail19/r61=11, phase504 at tail18/r61=11, and phase507 at
  tail19/r61=11
- the phase481 tail14/r61=10, phase485/481 low-tail+r61, and recent r61=10
  spread 5B energy bridge lanes completed without beating the repaired
  nonzero energy frontier of 652
- launched a phase499/500 r61=11 plus tail17/tail18 5B energy bridge at nonce
  835426; phase487, phase489, and phase499/500 energy lanes remain active
- exact refresh8 scanning continued into batches 160-223, and breadth scanning
  continued into phases 508-515 with start windows 533,549,565,581,597,613,
  629,645

May 23 continuation checkpoint 15:

- committed checkpoint 14 as bad6eed4 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 160-171 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 508-515 completed without a tail<=13 or r61<=8 move; this
  tranche mostly re-hit shifted versions of the recent low-tail and r61=10
  anchors
- phase508 rediscovered the phase476 r61=10 row; phase510 rediscovered the
  phase478 tail16 and r61=10 rows; phase513 rediscovered the phase481 tail14
  and r61=10 rows; phase514 rediscovered the phase482 r61=10 row
- phase509 rediscovered the phase477 tail17 row, phase511 rediscovered the
  phase479 tail17 row, phase512 rediscovered the phase480 tail16 row, and
  phase515 matched the phase499 tail17 plus r61=11 cluster
- the phase487 tail15/r61=10 and phase489 tail16/r61=11 5B energy bridge
  lanes completed without beating the repaired nonzero energy frontier of 652
- exact refresh8 scanning continued into batches 172-223, breadth scanning
  continued into phases 516-523 with start windows 661,677,693,709,725,741,
  757,773, and the phase499/500 energy lane remains active

May 23 continuation checkpoint 16:

- committed checkpoint 15 as 2a5299ff with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 172-179 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 516-523 completed without a tail<=13 or r61<=8 move; the
  strongest rows were still rediscoveries of known periodic anchors
- phase517 rediscovered the phase485 tail17 row and r61=10 row, phase519
  rediscovered the phase487 tail15 row and r61=10 row, phase521 rediscovered
  the phase489 tail16/r61=11 joint row, and phase522 rediscovered the phase490
  tail16 row
- the weaker phases bottomed out at phase516 tail18/r61=11, phase518
  tail19/r61=11, phase520 tail18/r61=11, and phase523 tail19/r61=11
- the phase499/500 r61=11 plus tail17/tail18 5B energy bridge completed
  without beating the repaired nonzero energy frontier of 652
- launched a phase520/488 r61=11 plus tail18 5B energy bridge at nonce
  835427; exact refresh8 scanning continued into batches 180-223, and breadth
  scanning continued into phases 524-531 with start windows 789,805,821,837,
  853,869,885,901

May 23 continuation checkpoint 17:

- committed checkpoint 16 as 6aa96933 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 180-189 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 524-531 completed without a tail<=13 or r61<=8 move; this
  tranche again mostly repeated known periodic anchors instead of opening a
  new frontier
- phase524 rediscovered the phase476/508 r61=10 row at window 7445, phase526
  rediscovered the phase478 tail16 and r61=10 pair, and phase530 rediscovered
  the phase482/514 r61=10 row
- phase525 rediscovered the phase477/493 tail17 plus r61=11 cluster, phase527
  rediscovered the phase479/495 tail17 plus r61=11 pair, and phase528
  rediscovered the phase480/512 tail16 row
- phase529's strongest low-tail row was the phase481/513 tail14 duplicate at
  window 3173, W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96; its
  best r61 row was the known r61=10 W1=0x2111,0x1574,0x256f family
- phase531 matched the phase499/515 tail17 row and r61=11 cluster, including
  W1=0x03b9,0x3c8c,0x1b93 at tail17 and r61=11 rows
  W1=0x238b,0x1963,0x1933, W1=0x13b1,0x1302,0x2fba, and
  W1=0x11be,0x3e10,0x1df9
- the phase520/488 r61=11 plus tail18 5B energy bridge remains active, exact
  refresh8 scanning continued into batches 190-223, and breadth scanning
  continued into phases 532-539 with start windows 917,933,949,965,981,997,
  1013,1029

May 23 continuation checkpoint 18:

- committed checkpoint 17 as fc7ad67b with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 190-197 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 532-539 completed without a tail<=13 or r61<=8 move; the
  scans remain dominated by periodic rediscoveries of the known anchors
- phase532 was weak, bottoming at tail18 and r61=11; phase534 was also weak,
  with only a single r61=11 row and no low-tail row below tail19
- phase533 rediscovered the phase485 r61=10 row
  W1=0x3a1f,0x39eb,0x15e9 and the phase485 tail17 row
  W1=0x16cd,0x3550,0x3a62
- phase535 rediscovered the phase487 tail15 row
  W1=0x2f1a,0x0a34,0x3867 and the phase487 r61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase536 re-hit the phase520/488 bridge cluster, bottoming at tail18 and
  four r61=11 rows, including W1=0x19d1,0x030f,0x39e8
- phase537 rediscovered the phase489 tail16/r61=11 joint row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase538 rediscovered the phase490/522 tail16 row
  W1=0x221b,0x3351,0x26a1 and the r61=11 row
  W1=0x2110,0x134a,0x283b; phase539 was weak, bottoming at tail19 and
  r61=11
- the phase520/488 r61=11 plus tail18 5B energy bridge remains active, exact
  refresh8 scanning continued into batches 198-223, and breadth scanning
  continued into phases 540-547 with start windows 1045,1061,1077,1093,1109,
  1125,1141,1157

May 23 continuation checkpoint 19:

- committed checkpoint 18 as 430be52e with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 198-205 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 540-547 completed without a tail<=13 or r61<=8 move; the
  scans continued the periodic re-hit pattern rather than opening a new
  SR=64 lead
- phase540 rediscovered the phase524 r61=10 row at window 7445,
  W1=0x061c,0x0522,0x2622; phases541 and 542 re-hit the phase493/525 and
  phase478/526 clusters
- phase543 was weak, bottoming at tail17 and r61=11; phase544 re-hit the
  phase480/512 tail16 row W1=0x1fb9,0x1bd0,0x3d14
- phase545 re-hit the phase481/513 tail14 row
  W1=0x3c4a,0x0174,0x205b and the known phase529 r61=10 family
  W1=0x2111,0x1574,0x256f
- phase546 re-hit the phase482/514/530 r61=10 row
  W1=0x0661,0x3b7a,0x37c3 and a phase530 joint row
  W1=0x06b7,0x2ed0,0x2ad6
- phase547 re-hit the phase499/515/531 tail17 row
  W1=0x03b9,0x3c8c,0x1b93 and the r61=11 cluster
  W1=0x238b,0x1963,0x1933, W1=0x13b1,0x1302,0x2fba, and
  W1=0x11be,0x3e10,0x1df9
- the phase520/488 r61=11 plus tail18 5B energy bridge completed without
  beating the repaired nonzero energy frontier of 652; the best row remains
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- launched a phase535/537/538/542 replacement energy lane at nonce 835428;
  exact refresh8 scanning continued into batches 206-223, and breadth scanning
  continued into phases 548-555 with start windows 1173,1189,1205,1221,1237,
  1253,1269,1285

May 23 continuation checkpoint 20:

- committed checkpoint 19 as 2bf3accb with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 206-213 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 548-555 completed without a tail<=13 or r61<=8 move; this
  tranche continued to map periodic copies of the known low-tail and r61
  anchors
- phase548 was weak, bottoming at tail18 and r61=11; phase550 was also weak,
  bottoming at tail19 and r61=11
- phase549 rediscovered the phase485/533 tail17 row
  W1=0x16cd,0x3550,0x3a62 and r61=10 row
  W1=0x3a1f,0x39eb,0x15e9
- phase551 rediscovered the phase487/535 tail15 row
  W1=0x2f1a,0x0a34,0x3867 and r61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase552 re-hit the phase536 bridge cluster: tail18
  W1=0x0956,0x2a04,0x2595 and r61=11 rows including
  W1=0x19d1,0x030f,0x39e8, W1=0x12bb,0x3816,0x1cef,
  W1=0x3dac,0x3510,0x262e, and W1=0x21a1,0x3fea,0x1f32
- phase553 rediscovered the phase489/537 tail16/r61=11 joint row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase554 rediscovered the phase490/522/538 tail16 row
  W1=0x221b,0x3351,0x26a1 and r61=11 row
  W1=0x2110,0x134a,0x283b
- phase555 was weak, bottoming at tail19 and r61=11
- the phase535/537/538/542 replacement energy lane remains active, exact
  refresh8 scanning continued into batches 214-223, and breadth scanning
  continued into phases 556-563 with start windows 1301,1317,1333,1349,1365,
  1381,1397,1413

May 23 continuation checkpoint 21:

- committed checkpoint 20 as 8fb6ecea with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 exact-only batches 214-215 completed with the same exact frontier:
  tail10, best_r61=9, best_joint=22/joint_max=11; the refresh8 plan has no
  pending batches beyond 215 in the current top640 file
- started the refresh8 xover32 exact-only pass over batches 0-63; batches 0-5
  completed with the same exact frontier and batches 6-7 remain active
- breadth phases 556-563 completed without a tail<=13 or r61<=8 move; the
  window sweep again primarily confirmed periodic copies of known anchor
  families
- phase556 rediscovered the phase524/540 r61=10 row at window 7445,
  W1=0x061c,0x0522,0x2622
- phase557 re-hit the phase541/525 cluster, bottoming at tail17 with
  W1=0x1a07,0x079d,0x129a and r61=11 rows including
  W1=0x37de,0x0132,0x3a37
- phase558 bottomed at tail16 with W1=0x1bf3,0x3294,0x21c7 and re-hit r61=10
  rows including W1=0x3d0a,0x1c32,0x04d9 and W1=0x0621,0x2b7e,0x3a81
- phase559 was weak overall, bottoming at tail17 and r61=11 without moving
  either frontier
- phase560 re-hit the phase480/512/544 tail16 row
  W1=0x1fb9,0x1bd0,0x3d14
- phase561 re-hit the phase481/513/545 tail14 row
  W1=0x3c4a,0x0174,0x205b and the known r61=10 family
  W1=0x2111,0x1574,0x256f
- phase562 re-hit the phase482/514/530/546 bridge, including the r61=10 row
  W1=0x0661,0x3b7a,0x37c3 and joint row W1=0x06b7,0x2ed0,0x2ad6
- phase563 re-hit the phase499/515/531/547 tail17 row
  W1=0x03b9,0x3c8c,0x1b93 and the r61=11 cluster
  W1=0x238b,0x1963,0x1933, W1=0x13b1,0x1302,0x2fba, and
  W1=0x11be,0x3e10,0x1df9
- the phase535/537/538/542 replacement energy lane remains active, exact
  xover32 scanning continued into batches 6-63, and breadth scanning
  continued into phases 564-571 with start windows 1429,1445,1461,1477,1493,
  1509,1525,1541

May 23 continuation checkpoint 22:

- committed checkpoint 21 as c06bddff with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 6-13 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 564-571 completed without a tail<=13 or r61<=8 move; this
  tranche again re-hit known periodic anchors and did not open a new SR=64
  lead
- phase564 was weak, bottoming at tail18 and r61=11
- phase565 rediscovered the phase485/533/549 tail17 row
  W1=0x16cd,0x3550,0x3a62 and r61=10 row
  W1=0x3a1f,0x39eb,0x15e9
- phase566 was weak, bottoming at tail19 and r61=11
- phase567 rediscovered the phase487/535/551 tail15 row
  W1=0x2f1a,0x0a34,0x3867 and r61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase568 re-hit the phase536/552 bridge cluster: tail18
  W1=0x0956,0x2a04,0x2595 and r61=11 rows including
  W1=0x19d1,0x030f,0x39e8, W1=0x12bb,0x3816,0x1cef,
  W1=0x3dac,0x3510,0x262e, and W1=0x21a1,0x3fea,0x1f32
- phase569 rediscovered the phase489/537/553 tail16/r61=11 joint row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase570 rediscovered the phase490/522/538/554 tail16 row
  W1=0x221b,0x3351,0x26a1 and r61=11 row
  W1=0x2110,0x134a,0x283b
- phase571 was weak, bottoming at tail19 and r61=11
- the phase535/537/538/542 replacement energy lane completed without beating
  the repaired nonzero energy frontier of 652; the best row remains
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- launched a phase556-564 replacement energy lane at nonce 835556; exact
  xover32 scanning continued into batches 14-63, and breadth scanning
  continued into phases 572-579 with start windows 1557,1573,1589,1605,1621,
  1637,1653,1669

May 23 continuation checkpoint 23:

- committed checkpoint 22 as 05cf70ac with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 14-21 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 572-579 completed without a tail<=13 or r61<=8 move; the
  block mainly confirmed the same periodic anchor families seen in the prior
  scan tranches
- phase572 rediscovered the phase524/540/556 r61=10 row at window 7445,
  W1=0x061c,0x0522,0x2622
- phase573 re-hit the phase557 cluster, bottoming at tail17 with
  W1=0x1a07,0x079d,0x129a and r61=11 rows including
  W1=0x37de,0x0132,0x3a37
- phase574 bottomed at tail16 with W1=0x1bf3,0x3294,0x21c7 and re-hit r61=10
  rows including W1=0x3d0a,0x1c32,0x04d9 and W1=0x0621,0x2b7e,0x3a81
- phase575 was weak overall, bottoming at tail17 and r61=11 without moving
  either frontier
- phase576 re-hit the phase480/512/544/560 tail16 row
  W1=0x1fb9,0x1bd0,0x3d14
- phase577 re-hit the phase481/513/545/561 tail14 row
  W1=0x3c4a,0x0174,0x205b and the known r61=10 family
  W1=0x2111,0x1574,0x256f
- phase578 re-hit the phase482/514/530/546/562 bridge, including the r61=10
  row W1=0x0661,0x3b7a,0x37c3 and joint row W1=0x06b7,0x2ed0,0x2ad6
- phase579 re-hit the phase499/515/531/547/563 tail17 row
  W1=0x03b9,0x3c8c,0x1b93 and the r61=11 cluster
  W1=0x238b,0x1963,0x1933, W1=0x13b1,0x1302,0x2fba, and
  W1=0x11be,0x3e10,0x1df9
- the phase556-564 replacement energy lane remains active, exact xover32
  scanning continued into batches 22-63, and breadth scanning continued into
  phases 580-587 with start windows 1685,1701,1717,1733,1749,1765,1781,1797

May 23 continuation checkpoint 24:

- committed checkpoint 23 as b79ff1ca with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 22-29 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 580-587 completed without a tail<=13 or r61<=8 move; the
  block again mostly re-hit established periodic anchors
- phase580 was weak, bottoming at tail18 and r61=11 without opening a new
  lead
- phase581 rediscovered the phase485/533/549/565 tail17 row
  W1=0x16cd,0x3550,0x3a62 and r61=10 row
  W1=0x3a1f,0x39eb,0x15e9
- phase582 was weak, bottoming at tail19 and r61=11 without moving either
  frontier
- phase583 rediscovered the phase487/535/551/567 tail15 row
  W1=0x2f1a,0x0a34,0x3867 and r61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase584 re-hit the phase536/552/568 bridge cluster: tail18
  W1=0x0956,0x2a04,0x2595 and r61=11 rows including
  W1=0x19d1,0x030f,0x39e8, W1=0x12bb,0x3816,0x1cef,
  W1=0x3dac,0x3510,0x262e, and W1=0x21a1,0x3fea,0x1f32
- phase585 rediscovered the phase489/537/553/569 tail16/r61=11 joint row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase586 rediscovered the phase490/522/538/554/570 tail16 row
  W1=0x221b,0x3351,0x26a1 and r61=11 row
  W1=0x2110,0x134a,0x283b
- phase587 was weak, bottoming at tail19 and r61=11 without moving either
  frontier
- the phase556-564 replacement energy lane completed without beating the
  repaired nonzero energy frontier of 652; the best row remains
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- launched a phase580-587 replacement energy lane at nonce 835580; exact
  xover32 scanning continued into batches 30-63, and breadth scanning
  continued into phases 588-595 with start windows 1813,1829,1845,1861,1877,
  1893,1909,1925

May 23 continuation checkpoint 25:

- committed checkpoint 24 as 65291dd8 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 30-39 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 588-595 completed without a tail<=13 or r61<=8 move; this
  block again mostly re-hit established phase-periodic anchors
- phase588 bottomed at tail19 and re-hit the phase540/556/572 r61=10 row
  W1=0x061c,0x0522,0x2622
- phase589 re-hit the phase557/573 tail17 row
  W1=0x1a07,0x079d,0x129a and r61=11 cluster row
  W1=0x3531,0x089d,0x1364
- phase590 re-hit the phase574 tail16 row W1=0x1bf3,0x3294,0x21c7 and
  r61=10 row W1=0x0621,0x2b7e,0x3a81
- phase591 was weak, bottoming at tail17 and r61=11 without moving either
  frontier
- phase592 re-hit the phase544/560/576 tail16 row
  W1=0x1fb9,0x1bd0,0x3d14, with best_r61 only 12
- phase593 re-hit the phase561/577 tail14 row
  W1=0x3c4a,0x0174,0x205b and r61=10 row
  W1=0x2111,0x1574,0x256f
- phase594 re-hit the phase562/578 r61=10 bridge row
  W1=0x0661,0x3b7a,0x37c3, while tail only reached 18
- phase595 re-hit the phase579 tail17 row W1=0x03b9,0x3c8c,0x1b93 and
  r61=11 rows including W1=0x11be,0x3e10,0x1df9
- the phase580-587 replacement energy lane is still active at nonce 835580;
  exact xover32 scanning continued into batches 40-63, and breadth scanning
  continued into phases 596-603 with start windows 1941,1957,1973,1989,2005,
  2021,2037,2053

May 23 continuation checkpoint 26:

- committed checkpoint 25 as 1cb0de12 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 40-47 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 596-603 completed without a tail<=13 or r61<=8 move; the
  block again tracked the same phase-periodic anchors
- phase596 was weak, bottoming at tail18 and r61=11 without moving either
  frontier
- phase597 re-hit the phase581 tail17 row W1=0x16cd,0x3550,0x3a62 and
  r61=10 row W1=0x3a1f,0x39eb,0x15e9
- phase598 was weak, bottoming at tail19 and r61=11 with an r61 row
  W1=0x2b91,0x378c,0x2b4e
- phase599 re-hit the phase583 tail15 row W1=0x2f1a,0x0a34,0x3867 and
  r61=10 row W1=0x37d3,0x23af,0x0f3a
- phase600 re-hit the phase584 bridge cluster: tail18
  W1=0x0956,0x2a04,0x2595 and r61=11 rows including
  W1=0x21a1,0x3fea,0x1f32
- phase601 re-hit the phase585 tail16/r61=11 joint row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase602 re-hit the phase586 tail16 row W1=0x221b,0x3351,0x26a1 and
  r61=11 row W1=0x2110,0x134a,0x283b
- phase603 was weak, bottoming at tail19 and r61=11 without moving either
  frontier
- the phase580-587 replacement energy lane is still active at nonce 835580;
  exact xover32 scanning continued into batches 48-63, and breadth scanning
  continued into phases 604-611 with start windows 2069,2085,2101,2117,2133,
  2149,2165,2181

May 23 continuation checkpoint 27:

- committed checkpoint 26 as 0ffd171f with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 48-55 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 604-611 completed without a tail<=13 or r61<=8 move; the
  block stayed on the known phase-periodic terrain
- phase604 bottomed at tail19 and re-hit the R61=10 row
  W1=0x061c,0x0522,0x2622
- phase605 re-hit the phase589/573 tail17 row
  W1=0x1a07,0x079d,0x129a and an r61=11 row
  W1=0x37de,0x0132,0x3a37
- phase606 re-hit the phase590/574 tail16 row
  W1=0x1bf3,0x3294,0x21c7 and R61=10 row
  W1=0x0621,0x2b7e,0x3a81
- phase607 re-hit a tail17 row W1=0x206f,0x25c0,0x1acf and an R61=11 row
  W1=0x3662,0x3c88,0x2ea2
- phase608 re-hit the phase592/576 tail16 row
  W1=0x1fb9,0x1bd0,0x3d14; best_r61 was only 12
- phase609 re-hit the phase593/577 tail14 row
  W1=0x3c4a,0x0174,0x205b and R61=10 row
  W1=0x2111,0x1574,0x256f
- phase610 re-hit the phase594/578 R61=10 row
  W1=0x0661,0x3b7a,0x37c3; tail only reached 18
- phase611 re-hit the phase595/579 tail17 row
  W1=0x03b9,0x3c8c,0x1b93 and an R61=11 row
  W1=0x11be,0x3e10,0x1df9
- the phase580-587 replacement energy lane completed its 5B budget without
  beating the repaired nonzero energy frontier of 652; the best row remains
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- launched a fresh phase604-610 replacement energy lane at nonce 835604, and
  breadth scanning continued into phases 612-619 with start windows 2197,
  2213,2229,2245,2261,2277,2293,2309 while exact xover32 scanning continued
  into batches 56-63

May 23 continuation checkpoint 28:

- committed checkpoint 27 as 2d7f3f3c with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- refresh8 xover32 exact-only batches 56-63 completed with the same exact
  frontier: tail10, best_r61=9, best_joint=22/joint_max=11
- breadth phases 612-619 completed without a tail<=13 or r61<=8 move
- phase612 bottomed at tail18 and R61=11; the R61 row re-hit
  W1=0x1c3c,0x3e29,0x107d
- phase613 re-hit the phase597/581 tail17 row
  W1=0x16cd,0x3550,0x3a62 and R61=10 row
  W1=0x3a1f,0x39eb,0x15e9
- phase614 bottomed at tail19 and R61=11, re-hitting the phase598 row
  W1=0x2b91,0x378c,0x2b4e
- phase615 re-hit the phase599/583 tail15 row
  W1=0x2f1a,0x0a34,0x3867 and R61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase616 re-hit the phase600/584 bridge cluster with tail18
  W1=0x0956,0x2a04,0x2595 and R61=11 rows including
  W1=0x21a1,0x3fea,0x1f32
- phase617 re-hit the phase601/585 joint row at tail16/R61=11:
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase618 re-hit the phase602/586 tail16 row W1=0x221b,0x3351,0x26a1
  and R61=11 row W1=0x2110,0x134a,0x283b
- phase619 bottomed at tail19 and R61=11 without moving either frontier
- the phase604-610 replacement energy lane is still active at nonce 835604;
  breadth scanning continued into phases 620-627 with start windows 2325,
  2341,2357,2373,2389,2405,2421,2437

May 23 continuation checkpoint 29:

- committed checkpoint 28 as cbdc8ecf with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- added a window selector for local-refinement batches and a local-refinement
  summarizer; rebuilt the reduced-n scanner with logging for refined R61 W
  witnesses so later logs distinguish scan registry rows from local-refined
  rows
- breadth phases 620-628 completed without a tail<=13 or r61<=8 move
- phase620 bottomed at tail19 and R61=10; the tail row was
  W1=0x26f0,0x1dfb,0x1b7a and the R61 row was
  W1=0x061c,0x0522,0x2622
- phase621 bottomed at tail17 and R61=11; the tail row was
  W1=0x1a07,0x079d,0x129a and the R61 row was
  W1=0x37de,0x0132,0x3a37
- phase622 bottomed at tail16 and R61=10; the tail row was
  W1=0x1bf3,0x3294,0x21c7 and the R61 row was
  W1=0x0621,0x2b7e,0x3a81
- phase623 bottomed at tail17 and R61=11; local refinement later found a
  tail16 row at window 69, W1=0x2b7c,0x0929,0x195f
- phase624 bottomed at tail16 and R61=12; local refinement improved selected
  R61 rows to 12 but did not beat the global R61 frontier
- phase625 was the best breadth hit in this block at tail14; local refinement
  improved several selected rows, including R61 14->12 at window 101, but did
  not beat the known R61=9 frontier
- phase626 bottomed at tail18 and R61=10; local refinement improved one
  selected R61 row from 13 to 11
- phase627 bottomed at tail17 and R61=11; local refinement had four improved
  rows, with selected bests staying at tail17 and R61=11
- phase628 bottomed at tail18 and R61=11; no selected registry row approached
  the exact tail10/R61=9 frontier
- the phase604-610 replacement energy lane remains active at nonce 835604;
  breadth scanning continued into phase629+ with start windows beginning at
  2469

May 23 continuation checkpoint 30:

- committed checkpoint 29 as 6b0d9bb0 with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- the phase604-610 replacement energy lane completed its 5B budget without
  improving the repaired nonzero energy frontier; best remained energy=652,
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- breadth phases 629-642 completed without a tail<=13 or r61<=8 move
- phase629 bottomed at tail17 and R61=10; phase630 reached tail19/R61=11
- phase631 re-hit the tail15 row W1=0x2f1a,0x0a34,0x3867 and an R61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase632 reached tail18/R61=11; phase633 re-hit the joint tail16/R61=11
  row W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase634 re-hit tail16 W1=0x221b,0x3351,0x26a1 and R61=11
  W1=0x2110,0x134a,0x283b
- phases635-640 stayed in the same terrain, with recurring R61=10 rows in
  phases636 and 638 and a phase640 tail16 row W1=0x1fb9,0x1bd0,0x3d14
- phase641 produced the best breadth hit in this block at tail14,
  W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96, plus an R61=10 row
  W1=0x2111,0x1574,0x256f
- phase642 bottomed at tail18 and R61=10, re-hitting
  W1=0x0661,0x3b7a,0x37c3 for the R61 row
- local refinement for phases629-638 did not move the global exact or joint
  frontiers; useful shaped rows included phase631 tail15/R61=13 and
  tail17/R61=10, phase633 tail19/R61=10, phase634 tail16/R61=12, phase636
  R61=10, and phase638 tail16/R61=13 plus two R61=10 rows
- selected phase640 and phase641 local-refinement windows are queued; phase639
  local refinement and the phase631-634 replacement energy lane are active,
  and breadth scanning continued into phase643

May 23 continuation checkpoint 31:

- committed checkpoint 30 as 1876111c with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- the phase631-634 replacement energy lane completed its 5B budget without
  improving the repaired nonzero energy frontier; best remained energy=652,
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- breadth phases 643-659 completed without a tail<=13 or r61<=8 move
- phase647 re-hit the tail15 row W1=0x2f1a,0x0a34,0x3867; local refinement
  shaped that window to R61=13 and also preserved a tail17/R61=10 selected row
- phase649 re-hit the joint tail16/R61=11 row W1=0x0221,0x2b8d,0x010d and
  local refinement repaired one selected R61 row to 10 at window 7397
- phase650 re-hit tail16 W1=0x221b,0x3351,0x26a1 and R61=11
  W1=0x2110,0x134a,0x283b; local refinement kept the tail16 row and repaired
  selected R61 rows to 11-12
- phase654 produced a tail16 row W1=0x1bf3,0x3294,0x21c7 and two R61=10 rows
  W1=0x0621,0x2b7e,0x3a81 and W1=0x3d0a,0x1c32,0x04d9; local refinement
  preserved those R61=10 rows but did not improve them
- phase657 produced the best breadth hit in this block at tail14,
  W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96, plus an R61=10 row
  W1=0x2111,0x1574,0x256f; local refinement preserved tail14 and repaired
  that tail row's local R61 witness from 15 to 13
- phase658 bottomed at tail18 and R61=10; local refinement kept the R61=10
  row W1=0x0661,0x3b7a,0x37c3 and repaired one selected R61 row from 13 to 11
- phase659 was weaker, bottoming at tail17 and R61=11
- a fresh phase657-seeded energy bridge is active at nonce 835634; phase659
  local refinement and breadth phases660-667 are active

May 23 continuation checkpoint 32:

- committed checkpoint 31 as 83dcb61c with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- the phase657-seeded replacement energy bridge completed its 5B budget without
  improving the repaired nonzero energy frontier; best remained energy=652,
  tail8/r61=9, d60=0x3126, gh60=0x4908f6a,
  W1=0x075d,0x24ea,0x2ccc and W2=0x066a,0x0ff9,0x2bd3
- breadth phases 660-680 completed without a tail<=13 or r61<=8 move
- phase663 and phase679 re-hit the tail15 row
  W1=0x2f1a,0x0a34,0x3867; phase679 also re-hit the R61=10 row
  W1=0x37d3,0x23af,0x0f3a
- phase665 and phase681 re-hit the joint tail16/R61=11 row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2
- phase666 re-hit tail16 W1=0x221b,0x3351,0x26a1 and R61=11
  W1=0x2110,0x134a,0x283b
- phase670 produced a tail16/R61=13 row W1=0x1bf3,0x3294,0x21c7 and
  preserved R61=10 rows W1=0x0621,0x2b7e,0x3a81 and
  W1=0x3d0a,0x1c32,0x04d9
- phase671 local refinement turned window 69 from scan tail22 into
  tail16/R61=12, W1=0x2b7c,0x0929,0x195f and
  W2=0x2a89,0x32ed,0x09d7
- phase672 local refinement preserved a tail16/R61=13 row at window 2133
  and improved window 2389 from scan tail22 to tail18/R61=12
- phase673 again produced the best breadth hit in this block at tail14,
  W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96; a 1B priority
  local refinement kept tail14 and improved that row's local R61 witness
  from 15 to 13
- phase674 local refinement produced a useful tail18/R61=11 row at window
  1653, W1=0x3f0d,0x1c98,0x148f and W2=0x3e1a,0x210b,0x32b1
- phase676 local refinement improved window 405 to tail18/R61=11,
  W1=0x2de2,0x350c,0x3800
- phase678 local refinement stayed weak, bottoming at tail19 and R61=11
- phase679 local refinement preserved the tail15 row and produced a useful
  tail17/R61=10 shaped row at window 7877,
  W1=0x2a95,0x1960,0x0a2d and W2=0x29a2,0x047c,0x38a5; it also preserved
  the R61=10 row W1=0x37d3,0x23af,0x0f3a at window 5061
- phase682 breadth completed with a tail16 row
  W1=0x221b,0x3351,0x26a1 and R61=11 at
  W1=0x2110,0x134a,0x283b; phase682 local-refinement windows have been
  selected
- phase680 and phase681 local refinement are active, and breadth scanning
  continued into phase683+

May 23 continuation checkpoint 33:

- breadth phases 683-687 completed without a tail<=13 or R61<=8 move
- phase681 local refinement preserved the joint tail16/R61=11 row
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2; it also shaped
  window 7397 to R61=10 with
  W1=0x365a,0x2a29,0x10a0 and W2=0x3567,0x2811,0x2f53
- phase682 local refinement preserved tail16 at window 6901 and improved that
  row's local R61 side to 12; it also preserved R61=11 at window 7669
- phase683 local refinement stayed weak, bottoming at tail19 and R61=11
- phase684 breadth and local refinement preserved the window 7445 R61=10 row
  W1=0x061c,0x0522,0x2622 and W2=0x0529,0x2729,0x3fbf; selected local
  refinement also shaped window 4373 from R61=15 to R61=12
- a second-stage 1B priority pass over phase681/window7397 and
  phase684/window7445 preserved both R61=10 rows but did not improve them
- phase685 breadth produced a tail17 row at window 4133 and R61=11 rows at
  windows 3877, 1829, and 5413; local refinement kept the tail17 row and
  improved its local R61 side to 13
- a seed-cap-512 priority pass over the tail-frontier windows preserved
  phase673/window3173 at tail14/R61=13 and phase679/window197 at tail15/R61=13
- phase686 breadth produced tail16 at window 5685 plus R61=10 rows at windows
  5429 and 7221; local refinement preserved tail16/R61=13 and both R61=10
  rows
- phase687 breadth produced a tail17 row at window 6725 and R61=11 rows at
  windows 837 and 5445; phase687 local refinement is active, and breadth
  scanning continued into phase688+

May 23 continuation checkpoint 34:

- committed checkpoint 33 as cafc518c with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- breadth phases 688-699 completed without a tail<=13 or R61<=8 move
- phase687 local refinement completed after checkpoint 33: window 69 improved
  from scan tail22 to tail16/R61=12, W1=0x2b7c,0x0929,0x195f and
  W2=0x2a89,0x32ed,0x09d7; window 6725 preserved tail17/R61=13
- phase688 local refinement preserved window 2133 at tail16/R61=13, preserved
  window 3669 at tail18/R61=12, and improved window 2389 from scan tail22
  to tail18/R61=12
- phase689 breadth re-hit the tail14 row
  W1=0x3c4a,0x0174,0x205b and W2=0x3b57,0x37bc,0x2a96; local refinement
  preserved tail14/R61=13 and the window 357 R61=10 row
- phase690 local refinement preserved the window 4725 R61=10 row
  W1=0x0661,0x3b7a,0x37c3 and improved the window 1653 tail18 row to
  R61=11; window 6005 improved from scan tail21 to tail19/R61=12
- phase691 local refinement kept the window 1925 tail17 row at R61=12 and
  preserved selected R61=11 rows at windows 3717, 4229, and 2181
- phase693 local refinement preserved the window 2725 R61=10 row
  W1=0x3a1f,0x39eb,0x15e9, improved window 7333 to tail17/R61=12, and
  improved window 5797 from R61=13 to R61=11
- phase694 local refinement preserved the window 437 R61=11 row and improved
  selected windows 6069 and 4021 to tail19/R61=12 and tail20/R61=12
- phase695 breadth produced a tail15 row at window 197 and an R61=10 row at
  window 5061; local refinement preserved tail15/R61=13 at window 197,
  preserved the window 5061 R61=10 row, and shaped window 7877 to
  tail17/R61=10
- phase696 local refinement preserved R61=11 rows at windows 7381, 4053,
  6613, and 725, with no tail-frontier move
- phase697 breadth produced a joint tail16/R61=11 row at window 6629,
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2; local refinement
  preserved that row and shaped window 7397 to R61=10
- phase698 local refinement preserved the window 6901 tail16 row and improved
  its local R61 side to 12; it also improved window 7669 from scan tail21 to
  tail19/R61=11
- phase699 was weaker, bottoming at tail19 and R61=11; local refinement
  preserved the window 6917 R61=11 row but did not improve it
- phase700 breadth re-hit the window 7445 R61=10 row
  W1=0x061c,0x0522,0x2622 and W2=0x0529,0x2729,0x3fbf; phase700 local
  refinement and breadth phase701 are active

May 23 continuation checkpoint 35:

- committed checkpoint 34 as 43011d2b with author and committer set to
  kodareef5 <kodareef5@users.noreply.github.com>
- breadth phases 700-715 completed without a tail<=13 or R61<=8 move
- phase700 local refinement preserved the window 7445 R61=10 row
  W1=0x061c,0x0522,0x2622 and W2=0x0529,0x2729,0x3fbf
- phase701 breadth/local preserved a tail17 row at window 4133 and R61=11
  rows at windows 3877, 1829, and 5413
- phase702 breadth/local preserved a tail16 row at window 5685 plus R61=10
  rows at windows 5429 and 7221
- phase703 breadth/local preserved a tail17 row at window 6725 and R61=11
  rows at windows 5445 and 837
- phase704 breadth/local preserved a tail16 row at window 2133
- phase705 breadth/local re-hit the tail14 row at window 3173 and preserved
  the window 357 R61=10 row
- phase706 local refinement preserved the window 4725 R61=10 row, improved
  window 1653 from R61=13 to R61=11, and improved window 6005 from scan
  tail21 to tail19/R61=12
- phase707 local refinement preserved the window 1925 tail17/R61=12 row and
  the selected R61=11 rows at windows 3717, 4229, and 2181; it also improved
  window 2437 from scan tail21 to tail19/R61=12
- phase708 local refinement improved window 405 from scan tail22 to
  tail18/R61=11, preserved tail18 rows at windows 1173 and 4757, and shaped
  windows 7317 and 1429 to R61=12
- phase709 local refinement preserved tail17 at window 7333, preserved the
  window 2725 R61=10 row, improved window 6309 to tail20/R61=11, and shaped
  window 5797 from R61=13 to R61=11
- phase710 local refinement was weaker, bottoming at tail19 and R61=11; it
  improved windows 4277 and 6069 to R61=12 while preserving the window 437
  R61=11 row
- phase711 breadth produced a tail15 row at window 197 and an R61=10 row at
  window 5061; local refinement preserved window 197 at tail15/R61=13,
  preserved window 5061 at R61=10, shaped window 7877 to tail17/R61=10, and
  improved window 3269 to R61=11
- phase712 local refinement did not move the frontier; it preserved a tail18
  row at window 7893, an R61=11 row at window 7381, and selected R61=11 rows
  at windows 4053, 6613, and 725
- phase713 breadth produced and local refinement preserved the joint
  tail16/R61=11 row at window 6629,
  W1=0x0221,0x2b8d,0x010d and W2=0x012e,0x2f07,0x38d2; local refinement
  also shaped window 7397 to R61=10 and window 5861 to R61=11
- phase714 breadth produced a tail16/R61=14 row at window 6901; local
  refinement preserved tail16 and improved its local R61 side to 12, and
  improved window 7669 from scan tail21 to tail19/R61=11
- phase715 was weaker, bottoming at tail19 and R61=11; local refinement
  preserved the window 6917 R61=11 row and did not improve the frontier
