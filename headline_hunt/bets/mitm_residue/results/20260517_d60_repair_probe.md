# D60 Low-HW Repair Probe

The exact three-free-word interface currently enforces `D60=0`: choose
`W57..W59`, derive the paired lane words that zero the selected late-state
differences, and only score tails when the round-60 schedule defect is exactly
zero.

This probe asks a narrower question: what if a small nonzero `D60` could be
repaired by one additional shaping degree of freedom at `W60`? It does not claim
the extra word has been constructed. It scores the conditional surface:

```text
scan candidate has D60 != 0 and HW(D60) <= k
pretend W60_2 can be changed to the required value
resimulate rounds 60..63 and retain repaired tail/r61 witnesses
```

That is a useful test because it separates two failure modes:

```text
low-HW D60 repair still has random tails  -> extra interface probably weak
low-HW D60 repair exposes lower tails     -> worth building the actual repair map
```

## Controls

N=8 exact repair smoke:

```text
exact best tail in sample = HW12
repair probe k=1          = repaired tail HW8, repaired r61 HW6
best repaired D60         = 0x4
```

This is the intended proof of signal. The probe can find better conditional
tails when a small schedule defect is patched at the interface.

## N=14 k=1 Probe

Command shape:

```text
N=14 prefix_limit=32768 refine_seed_cap=64 mode=repair repair_hw_limit=1
windows = 1648,496,1584,73,50,5808
```

Result:

```text
repair candidates = 2,742,976
best exact tail   = HW16
best repaired tail = HW15
```

Best repaired-tail witness:

```text
sample_start=2392064 window=73
tail=15 r61=17 d60=0x4 d60_hw=1 gh60=0xcedbd9a
W1=0x10c9,0x19f6,0x752
W2=0xfd6,0x2a9e,0x961
```

Best repaired-r61 witness:

```text
sample_start=54001664 window=1648
r61=11 tail=22 d60=0x800 d60_hw=1 gh60=0x4909b6e
W1=0x21df,0x3d40,0x2949
W2=0x20ec,0x3553,0x2717
```

## N=14 k=2 Probe

Command shape:

```text
N=14 prefix_limit=32768 refine_seed_cap=64 mode=repair repair_hw_limit=2
windows = 73,1584,1648,496
```

Result:

```text
repair candidates  = 13,731,684
best repaired tail = HW15
best repaired r61  = HW10
```

Best repaired-tail witnesses:

```text
sample_start=54001664 window=1648
tail=15 r61=16 d60=0xa00 d60_hw=2 gh60=0x55e84a6
W1=0x3a43,0xe5e,0x309f
W2=0x3950,0xadb,0x4fa

sample_start=2392064 window=73
tail=15 r61=17 d60=0x4 d60_hw=1 gh60=0xcedbd9a
W1=0x10c9,0x19f6,0x752
W2=0xfd6,0x2a9e,0x961
```

Best repaired-r61 witnesses:

```text
sample_start=16252928 window=496
r61=10 tail=21 d60=0x18 d60_hw=2 gh60=0x4a047fa
W1=0x39a,0x11fc,0x2f40
W2=0x2a7,0x741,0x384d

sample_start=16252928 window=496
r61=10 tail=25 d60=0x1800 d60_hw=2 gh60=0x44845a6
W1=0x14bc,0x30ac,0x31ba
W2=0x13c9,0x36e2,0x95c
```

## N=14 k=3 Probe

Command shape:

```text
N=14 prefix_limit=32768 refine_seed_cap=64 mode=repair repair_hw_limit=3
windows = 73,496,1584,1648,1744,6992
```

Result:

```text
repair candidates  = 92,158,389
best repaired tail = HW11
best repaired r61  = HW10
```

Best repaired-tail witnesses:

```text
sample_start=57147392 window=1744
tail=11 r61=20 d60=0xc d60_hw=2 gh60=0xfb3c4aa
W1=0x1542,0x235f,0x2efe
W2=0x144f,0x3a34,0x24ea

sample_start=54001664 window=1648
tail=13 r61=11 d60=0x45 d60_hw=3 gh60=0x38984aa
W1=0x2531,0x33e6,0x39a5
W2=0x243e,0x3aa6,0x35f4

sample_start=2392064 window=73
tail=13 r61=18 d60=0x58 d60_hw=3 gh60=0xf8dfbbe
W1=0x2db8,0x16a0,0x1dca
W2=0x2cc5,0x3fa4,0x1e8a
```

Best repaired-r61 witnesses:

```text
sample_start=57147392 window=1744
r61=10 tail=20 d60=0x1108 d60_hw=3 gh60=0x492849e
W1=0x1b47,0x296b,0x2d6c
W2=0x1a54,0x3956,0x16e1

sample_start=16252928 window=496
r61=10 tail=21 d60=0x18 d60_hw=2 gh60=0x4a047fa
W1=0x39a,0x11fc,0x2f40
W2=0x2a7,0x741,0x384d
```

## N=14 k=4/k=5 Focused Probes

Command shape:

```text
N=14 prefix_limit=32768 refine_seed_cap=64 mode=repair
k=4 windows = 1744,1648,73,496
k=5 windows = 1744,1648,73,496
```

Result:

```text
k=4 repair candidates = 192,537,508
k=5 repair candidates = 454,933,980
best repaired tail    = HW10
best repaired r61     = HW9
```

Best repaired-tail witnesses:

```text
sample_start=2392064 window=73
tail=10 r61=15 d60=0x88a d60_hw=4 gh60=0xce644e6
W1=0x1214,0x378e,0x2ff8
W2=0x1121,0x176,0x62e

sample_start=16252928 window=496
tail=10 r61=15 d60=0xc0b d60_hw=5 gh60=0xc979fae
W1=0x1faf,0x945,0xad9
W2=0x1ebc,0x3d9c,0x8b8
```

Best repaired-r61 witnesses:

```text
sample_start=2392064 window=73
r61=9 tail=23 d60=0x2188 d60_hw=4 gh60=0x460bfea
W1=0x2f8d,0x1d68,0x25d8
W2=0x2e9a,0x38f7,0x2c90

sample_start=54001664 window=1648
r61=9 tail=20 d60=0x2305 d60_hw=5 gh60=0x490bb6a
W1=0xd4d,0x21ea,0x5f3
W2=0xc5a,0x3fe5,0x1b11
```

The k=5 expansion added more HW10/HW9 handles but did not improve beyond the
k=4 frontier in the focused four-window set.

## Read

The repair surface is not a closure yet. It did not produce a joint tail/r61
handle near SR64. But it did improve the conditional N=14 tail frontier from
exact HW16 to repaired HW10, and k=4/k=5 expose repaired r61-HW9 handles.

That makes the next algebraic build concrete:

```text
1. Treat D60 low-HW rows as targets, not discarded misses.
2. Derive which upstream/free-word perturbations can realize req_w2_60.
3. Keep W57..W59 as the address system and add one real repair variable.
4. Promote rows where repaired tail <= 10 or repaired r61 <= 9 into focused
   local search over the true repair variable.
```

The key risk is false optimism: `eval_repaired_tail` edits `W60_2` directly, so
it ignores whether the SHA-256 message schedule can actually realize that edit
without damaging earlier constraints. The evidence level is therefore
conditional, but it is a better next front than plain random N=14 breadth alone.
