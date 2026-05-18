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

Active follow-up lanes:

- `20260517_nonzero939_bridge_energy_prefix2_1b.log`
- `20260517_nonzero865_bridge_energy_prefix2_1b.log`
- `20260517_nonzero865_solo_energy_prefix2_1b.log`
