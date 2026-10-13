#!/usr/bin/env python3
"""Nine GF(2) schemes, <2,5,6;47> x 3 and <3,5,5;58> x 6: exact verification, an invariant of the equivalence
group G, and the comparison with the public schemes of these two formats.
Report: research/2026-10-13_gf2_scheme_classes.md (the group G, the invariance proof, the pinned public files).

What it does (standard library plus search/gf2mm.py; deterministic; no output depends on time or paths):
  1. reads the nine files in search/schemes/gf2-2x5x6-3x5x5/ and checks: exactly the keys format, field, rank,
     convention, terms, products; rank = number of terms, all terms distinct, no zero factor; both exact verifiers
     of search/gf2mm.py (verify, verify_explicit); every products string equals gf2mm.describe_term of its term;
  2. the format maps c: (U,V,W) -> (V,W,U) and t: (U,V,W) -> (W^T,V^T,U^T): the six words id, c, cc, t, tc, tcc
     send (n,m,p) to its six permutations; a word other than id fixes (n,m,p) iff two of n, m, p are equal
     (checked for all formats with entries 1..6); for (2,5,6) only id, for (3,5,5) exactly id and t; every word
     maps the standard algorithm and every one of the nine schemes to a valid scheme of the image format;
  3. the invariant kappa: the multiset over the terms of the GF(2) ranks (rk U, rk V, rk W); for <3,5,5> the key
     is (rk V, min(rk U, rk W), max(rk U, rk W)) (the 3x5 and 5x3 slots symmetrised). It must be unchanged by 30 random
     sandwiches (P, Q, S) per scheme (fixed generator, random.Random(20261013)) and, for <3,5,5>, by t;
  4. the nine invariants must be pairwise different within each format;
  5. comparison with the 33 public representations of these formats listed in PUBLIC (section 3 of the report):
     - offline (default): with the RECORDED invariants below, which a run with --cache computes from the pinned
       files and checks; every line that uses them says "recorded";
     - with --cache DIR (and --download to fetch missing files into DIR, which must lie outside the repository):
       each file's SHA-256 must equal its pin; it is parsed, validated exactly over Q (for the two GF(2)-only
       representations: over GF(2)) in exactly one reading of its third factor, reduced mod 2 (refused if a
       denominator is even), brought to the target format by the words of step 2, validated by both exact
       verifiers, and its invariant and its GF(2) term set must equal the recorded ones; three primary copies
       (ALIASES: the two Lille catalogue files, the flips repository file) must be byte-identical to pinned files;
  6. negative controls: a one-bit change in a scheme is rejected by both verifiers; a non-symmetry (U -> P U alone)
     maps the standard algorithm to an invalid scheme; the unsymmetrised <3,5,5> multiset changes under t for some
     of the six (so the symmetrisation is needed); the comparison reports a coincidence when one own invariant is
     planted among the public ones; with --cache: a copy with one changed byte fails its SHA-256 pin, and each of
     the two GF(2)-only representations (AlphaTensor's GF(2) scheme for <3,5,5>) fails the exact validation over Q
     in both readings.
Every check prints one [PASS]/[FAIL] line; the last lines give the work done; exit code 0 only if every check
passes.

Usage (from the repository root):
    python experiments/2026-10-13_gf2_scheme_classes.py                            # offline, recorded invariants
    python experiments/2026-10-13_gf2_scheme_classes.py --cache DIR                # read the pinned files from DIR
    python experiments/2026-10-13_gf2_scheme_classes.py --cache DIR --download     # fetch missing files into DIR
With --cache a file is read from DIR/<sha1 hex of its URL> or, if that does not exist, DIR/<its file name>, and used
only if its SHA-256 equals the pin; --download stores a missing file as DIR/<sha1 hex of its URL>, at most one request
per second, sending nothing but the URL and a User-Agent that names this script.
Third-party files are never copied into the repository. The AlphaTensor .npz files hold pickled object arrays;
they are decoded statically (pickletools.genops lists the opcodes; nothing is unpickled, no object is built).
"""
from __future__ import annotations

import argparse
import ast
import bz2
import hashlib
import io
import json
import pickletools
import random
import re
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from search import gf2mm  # noqa: E402

SCHEME_DIR = REPO / "search" / "schemes" / "gf2-2x5x6-3x5x5"
OWN = {(2, 5, 6): (47, 3), (3, 5, 5): (58, 6)}       # format: (rank, number of files)
USER_AGENT = "complexity-pairs-dataset experiments/2026-10-13_gf2_scheme_classes.py (python urllib)"

RAW = "https://raw.githubusercontent.com/"
FMM = RAW + "dronperminov/FastMatrixMultiplication/7e3ac35ca92cb30d568519ea63d7a1accad2c908/schemes/"
MMC = RAW + "solven-eu/matmulcatalog/796a102adde213c966ec5d0e307b9794c8f131d5/src/main/resources/schemes/"
ATR = RAW + "google-deepmind/alphatensor/1949163da3bef7e3eb268a3ac015fd1c2dbfc767/algorithms/"
AER = RAW + "google-deepmind/alphaevolve_results/4226acbf237ff9ad10ba7673a2af127a2d8a5971/"

# id, target format, URL, SHA-256 of the file, reader, published format, extra (npz member / notebook variable),
# gf2_only (the representation is valid over GF(2) only)
PUBLIC = [
    ("pub01", (2, 5, 6), FMM + "results/serendipitous_base/2x5x6_m47_5ec0a82ac73bd3bfcc87c60784674ec9d83c136c_Z.json",
     "25b4224aaaf7ddad788cb3504c44e43b0caa8b91dde557a9d3a368676d074724", "json", (2, 5, 6), None, False),
    ("pub02", (2, 5, 6), FMM + "results/serendipitous_base/2x5x6_m47_66ab3aeb9f74d7da872f7af3eb496edad7068432_Q.json",
     "11ec534fb1f7c59e3e1e05b4cbbcedccb9a991a3f8482ba79aacb933e79c2116", "json", (2, 5, 6), None, False),
    ("pub03", (2, 5, 6), FMM + "results/addition_reduced_ZT/2x5x6_m47_cr181_fv63_cn332_ZT_reduced.json",
     "3fa1d3759dbc1fec75c4330046151e028ef5cccaaebb70e7b936db4d0ecd5db9", "json", (2, 5, 6), None, False),
    ("pub04", (2, 5, 6), FMM + "known/alpha_evolve/2x5x6_m47_mod0.json",
     "d8b8e9b5e824fa2209b386bf8e0489552d74ac9e19db54de9c3704ce6f018412", "json", (2, 5, 6), None, False),
    ("pub05", (2, 5, 6), FMM + "known/tensor/2x5x6_tensor.mpl",
     "5b16e1eafb8a6d4c339cd8682dd587f97ee3f46d77121284cf2f7007859e30fc", "mpl", (2, 5, 6), None, False),
    ("pub06", (2, 5, 6), MMC + "known/section6/2x5x6-r47-alphaevolve-7387644.json",
     "845c095266688f7a5c5d16bd4cf5aa22c9e42c4f7ac334bdf41f7f01a73a9e8b", "json", (2, 5, 6), None, False),
    ("pub07", (2, 5, 6), MMC + "known/section6/2x5x6-r47-perminov_cr181_fv63_cn332_ZT_reduced-413a41d.json",
     "72a1dad64ae219c19d0296b9fc8b0a28aa2c01a3dedbbf7ed123efa492b65fa5", "json", (2, 5, 6), None, False),
    ("pub08", (2, 5, 6), MMC + "bud-bases/section6/2x5x6-r47-perminov_serbase_Q-087c8a7.json",
     "f144f7bd98d2bc6822fbb1867f3dd5741e2d4ccd9667f59d616246906559c3da", "json", (2, 5, 6), None, False),
    ("pub09", (2, 5, 6), MMC + "bud-bases/section6/2x5x6-r47-perminov_serbase_Z-5962adf.json",
     "02fc00070946faf600fb45d7e81c5b926104a741b724a71c5c3827da8702fe35", "json", (2, 5, 6), None, False),
    ("pub10", (2, 5, 6), MMC + "derived/section6/2x6x5-r47-derived-999879e.json",
     "761990d48cde98fd167196d5999cb92eb74116bd6df5811d258491839a63751a", "json", (2, 6, 5), None, False),
    ("pub11", (2, 5, 6), AER + "mathematical_results.ipynb",
     "2cce2543e48c89aa3e91614272a698a0147dd2548ea11cf92f1292b7435d38ff", "notebook", (2, 5, 6),
     "decomposition_256", False),
    ("pub12", (3, 5, 5), FMM + "results/serendipitous_base/3x5x5_m58_506f8f6eb3be5c9dc28e5ed69a03660f55b50fc2_ZT.json",
     "08d04ded2273abeb3617f9d30ef552d19ef2f1c05f919c2d43755772ff19cf25", "json", (3, 5, 5), None, False),
    ("pub13", (3, 5, 5), FMM + "known/alpha_tensor/3x5x5_m58_ZT.json",
     "5aac12f4f62c455b5aaf6c5e46ec80cc5ad04a6da87c8e3c93ccd5f259a9b24d", "json", (3, 5, 5), None, False),
    ("pub14", (3, 5, 5), FMM + "results/naive_addition_reduced_ZT/3x5x5_m58_c351_ZT.json",
     "4204984a7237ea50401f98191ca6f7ff09a0827935558e410f03b9158c64f8e9", "json", (3, 5, 5), None, False),
    ("pub15", (3, 5, 5), FMM + "results/naive_addition_reduced_ZT/3x5x5_m58_c351_ZT.m",
     "3e4140d9e2cbe7d53d9c80f3ac198ab5a3f70cbf15d71eb2b5326a6d19326aea", "mathematica", (3, 5, 5), None, False),
    ("pub16", (3, 5, 5), FMM + "results/addition_reduced_ZT/3x5x5_m58_cr221_cn357_ZT_reduced.json",
     "17cdcab30fdacdaf92464bbfd7ff135a1d39fada357114d400586e8cad1dcd9e", "json", (3, 5, 5), None, False),
    ("pub17", (3, 5, 5), FMM + "results/serendipitous_base/3x5x5_m58_e3fdc8efb89aac032c6eb9901d691bef1a0f61db_ZT.json",
     "665074e6c7791ad7c3300afc559ac95123dbe3c2316843825f91e633fcc888fd", "json", (3, 5, 5), None, False),
    ("pub18", (3, 5, 5), FMM + "known/tensor/3x5x5_tensor.mpl",
     "906145e2716e693b72e4a0f74d52bbfb9bebbf25b45c100e0a2f064385f39d7a", "mpl", (3, 5, 5), None, False),
    ("pub19", (3, 5, 5), FMM + "known/jakobmoosbauer_flips/355-58-mod0.exp",
     "321fa23a1726922ea3ec5183248a3168833e7b3d2b794f5458c09a1cb09cbf1d", "exp", (3, 5, 5), None, False),
    ("pub20", (3, 5, 5), FMM + "known/jakobmoosbauer_flips/355-58-mod0.m",
     "9a93f226b472e06e4a12f2c1c44c26d0821a95cee5fb3e101e9a3babe17b72b0", "mathematica", (3, 5, 5), None, False),
    ("pub21", (3, 5, 5), FMM + "known/fmm_add_reduction/Moosbauer-355-58-mod0.exp",
     "321fa23a1726922ea3ec5183248a3168833e7b3d2b794f5458c09a1cb09cbf1d", "exp", (3, 5, 5), None, False),
    ("pub22", (3, 5, 5), FMM + "known/fmm_add_reduction/Moosbauer-355-58-mod0.m",
     "9a93f226b472e06e4a12f2c1c44c26d0821a95cee5fb3e101e9a3babe17b72b0", "mathematica", (3, 5, 5), None, False),
    ("pub23", (3, 5, 5), MMC + "known/section5/3x5x5-r58-alphatensor_F2-84728a0.json",
     "beb550a29f18b20f0f794cf41626dcd6f5131df26db6623d0b6d026706f4f104", "json", (3, 5, 5), None, True),
    ("pub24", (3, 5, 5), MMC + "known/section5/3x5x5-r58-alphatensor_Z-263818a.json",
     "6f223758a99ff79b458e0c833a728398f9350ce0d9a7d8bedd2c23e28ed7a5b9", "json", (3, 5, 5), None, False),
    ("pub25", (3, 5, 5), MMC + "known/section5/3x5x5-r58-flips_mod0-e8c5fec.json",
     "92179dda19d947cafd51164b66adac913944da9b67fd489fada397f426ba2300", "json", (3, 5, 5), None, False),
    ("pub26", (3, 5, 5), MMC + "known/section5/3x5x5-r58-perminov_c351_ZT-093b3cc.json",
     "8a2e9b4683d7ced9f553ae6fb6c9eb1cc0696cfb670bbc19b2ba5c37077b3511", "json", (3, 5, 5), None, False),
    ("pub27", (3, 5, 5), MMC + "known/section5/3x5x5-r58-perminov_cr221_cn357_ZT_reduced-f890d6a.json",
     "64799c13324fceec2451bf59cc736846cfc1c178b8d675048c2b031f73e7c5e1", "json", (3, 5, 5), None, False),
    ("pub28", (3, 5, 5), MMC + "bud-bases/section5/3x5x5-r58-perminov_serbase_ZT-c249478.json",
     "2557e3edd84daa8af2925d08d9af55ba2e63f04e32f14713f8efe48dd55dd243", "json", (3, 5, 5), None, False),
    ("pub29", (3, 5, 5), MMC + "bud-bases/section5/3x5x5-r58-perminov_serbase_ZT-ef75e42.json",
     "f995d1c2b5e3dfff31e21b75bc7725d72d4d94cbd86ccf4883ca4a013d333785", "json", (3, 5, 5), None, False),
    ("pub30", (3, 5, 5), MMC + "derived/section5/5x3x5-r58-derived-72507fc.json",
     "bad65c245042ae76d34600148f5a5c430f834dc0bae5e836ca9f766aa1a9ab02", "json", (5, 3, 5), None, False),
    ("pub31", (3, 5, 5), MMC + "derived/section5/5x5x3-r58-derived-e1f0adb.json",
     "c07d93aa5454a6ded56df45e905d41f49c4a7761080aa200d5c525c02c75ac47", "json", (5, 5, 3), None, False),
    ("pub32", (3, 5, 5), ATR + "factorizations_f2.npz",
     "70f09f349d8d2874ef0e0e089459c7320f5aa3eef277df5ffa67f573709db2da", "npz", (3, 5, 5), "3,5,5.npy", True),
    ("pub33", (3, 5, 5), ATR + "factorizations_r.npz",
     "4d59571a2537a9472e8229176d5ebe2925f3e041ad403c095b41853026caec33", "npz", (3, 5, 5), "3,5,5.npy", False),
]

# Primary copies of three pinned files, checked with --cache: (pinned id, URL, SHA-256 of the file at the URL,
# compression). The content (decompressed for .bz2) must be byte-identical to the pinned file.
ALIASES = [
    ("pub05", "https://fmm.univ-lille.fr/2x5x6_tensor.mpl.bz2",
     "a48774adf5a8975f1cfcdd94f307506bc5e84074733296b425ecada8d7193f1b", "bz2"),
    ("pub18", "https://fmm.univ-lille.fr/3x5x5_tensor.mpl.bz2",
     "de4cf95066235ba5e29a3c102c48a6bcf9049bac23572b8c5d5294ffedd0a296", "bz2"),
    ("pub19", RAW + "jakobmoosbauer/flips/e31a0a0f0d2577cee5da047ca7dcae0c61992e40/solutions/355-58-mod0.exp",
     "321fa23a1726922ea3ec5183248a3168833e7b3d2b794f5458c09a1cb09cbf1d", None),
]

# RECORDED: the results of a run with --cache on the pinned files (2026-10-13; printed by --print-recorded). Offline
# mode compares the nine schemes with these; a run with --cache recomputes every row and checks it equals this table.
# id -> (reading of the third factor, invariant kappa, first 16 hex digits of the SHA-256 of the canonical GF(2) term
# set: the minimum over the orientations to the target format of the sorted term list in the bit layout of gf2mm)
RECORDED = {
    "pub01": ("ki", "{(1,1,1):18, (1,2,1):1, (1,3,1):6, (1,4,1):7, (1,5,1):2, (2,2,2):9, (2,4,2):4}",
              "d3d174ecd43968e9"),
    "pub02": ("ki", "{(1,1,1):17, (1,2,1):3, (1,3,1):6, (1,4,1):7, (1,5,1):1, (2,2,2):9, (2,4,2):4}",
              "2846122de30ba0bf"),
    "pub03": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub04": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub05": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub06": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub07": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub08": ("ki", "{(1,1,1):17, (1,2,1):3, (1,3,1):6, (1,4,1):7, (1,5,1):1, (2,2,2):9, (2,4,2):4}",
              "2846122de30ba0bf"),
    "pub09": ("ki", "{(1,1,1):18, (1,2,1):1, (1,3,1):6, (1,4,1):7, (1,5,1):2, (2,2,2):9, (2,4,2):4}",
              "d3d174ecd43968e9"),
    "pub10": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub11": ("ki", "{(1,1,1):18, (1,2,1):4, (1,3,1):8, (1,4,1):4, (2,2,2):11, (2,4,2):2}",
              "f11c063440604d3c"),
    "pub12": ("ki", "{(1,1,1):16, (1,1,2):1, (1,2,2):4, (2,1,1):11, (2,2,2):13, (3,1,1):9, (3,2,2):3, (4,1,1):1}",
              "015cdcbc61b41f1c"),
    "pub13": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):10, (2,1,2):7, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "1f5b8256995447ad"),
    "pub14": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):16, (3,1,1):3}",
              "8e9b1a61b6a1e6f0"),
    "pub15": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):16, (3,1,1):3}",
              "8e9b1a61b6a1e6f0"),
    "pub16": ("ki", "{(1,1,1):7, (1,1,2):2, (1,1,3):10, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):17, (4,1,1):2}",
              "a2f27f9414010593"),
    "pub17": ("ki", "{(1,1,1):15, (1,1,2):1, (1,2,2):5, (2,1,1):11, (2,2,2):12, (3,1,1):7, (3,1,2):2, (4,1,1):2, (4,2,2):3}",
              "72dc819e18c3564c"),
    "pub18": ("ki", "{(1,1,1):7, (1,1,2):2, (1,1,3):10, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):17, (4,1,1):2}",
              "a2f27f9414010593"),
    "pub19": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):10, (2,1,2):6, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "5954aefb140af604"),
    "pub20": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):10, (2,1,2):6, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "5954aefb140af604"),
    "pub21": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):10, (2,1,2):6, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "5954aefb140af604"),
    "pub22": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):10, (2,1,2):6, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "5954aefb140af604"),
    "pub23": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):6, (2,1,2):4, (2,1,3):4, (2,2,2):17, (3,1,1):5, (3,1,2):1, (4,1,1):1}",
              "580a5b771ab98791"),
    "pub24": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):10, (2,1,2):7, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "1f5b8256995447ad"),
    "pub25": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):10, (2,1,2):6, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "5954aefb140af604"),
    "pub26": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):16, (3,1,1):3}",
              "8e9b1a61b6a1e6f0"),
    "pub27": ("ki", "{(1,1,1):7, (1,1,2):2, (1,1,3):10, (2,1,1):14, (2,1,2):4, (2,1,3):2, (2,2,2):17, (4,1,1):2}",
              "a2f27f9414010593"),
    "pub28": ("ki", "{(1,1,1):16, (1,1,2):1, (1,2,2):4, (2,1,1):11, (2,2,2):13, (3,1,1):9, (3,2,2):3, (4,1,1):1}",
              "015cdcbc61b41f1c"),
    "pub29": ("ki", "{(1,1,1):15, (1,1,2):1, (1,2,2):5, (2,1,1):11, (2,2,2):12, (3,1,1):7, (3,1,2):2, (4,1,1):2, (4,2,2):3}",
              "72dc819e18c3564c"),
    "pub30": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):10, (2,1,2):7, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "1f5b8256995447ad"),
    "pub31": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):10, (2,1,2):7, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "1f5b8256995447ad"),
    "pub32": ("ki", "{(1,1,1):4, (1,1,2):4, (1,1,3):10, (1,2,2):1, (1,2,3):1, (2,1,1):6, (2,1,2):4, (2,1,3):4, (2,2,2):17, (3,1,1):5, (3,1,2):1, (4,1,1):1}",
              "580a5b771ab98791"),
    "pub33": ("ki", "{(1,1,1):5, (1,1,2):2, (1,1,3):10, (1,2,2):2, (2,1,1):10, (2,1,2):7, (2,1,3):2, (2,2,2):16, (3,1,1):4}",
              "1f5b8256995447ad"),
}

FAILURES = []
WORK = Counter()


def say(line=""):
    print(line)


def check(label, ok, detail=""):
    say(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------ GF(2) matrices
def rows_of(x, r, c):
    """Row bitmasks of the r x c matrix stored in x (entry (i, j) is bit i*c + j)."""
    mask = (1 << c) - 1
    return [(x >> (i * c)) & mask for i in range(r)]


def from_rows(rs, c):
    x = 0
    for i, row in enumerate(rs):
        x |= row << (i * c)
    return x


def rank2(x, r, c):
    basis = {}
    for v in rows_of(x, r, c):
        while v:
            hb = v.bit_length() - 1
            if hb in basis:
                v ^= basis[hb]
            else:
                basis[hb] = v
                break
    return len(basis)


def transpose(x, r, c):
    """The c x r transpose of the r x c matrix x."""
    out = 0
    for i in range(r):
        for j in range(c):
            if (x >> (i * c + j)) & 1:
                out |= 1 << (j * r + i)
    return out


def matmul2(x, y, r, s, t):
    """(r x s) times (s x t) over GF(2)."""
    yr = rows_of(y, s, t)
    out = []
    for row in rows_of(x, r, s):
        acc = 0
        while row:
            low = row & -row
            acc ^= yr[low.bit_length() - 1]
            row ^= low
        out.append(acc)
    return from_rows(out, t)


def inverse2(x, d):
    rs = rows_of(x, d, d)
    aug = [rs[i] | (1 << (d + i)) for i in range(d)]
    for col in range(d):
        piv = next((i for i in range(col, d) if (aug[i] >> col) & 1), None)
        if piv is None:
            return None
        aug[col], aug[piv] = aug[piv], aug[col]
        for i in range(d):
            if i != col and (aug[i] >> col) & 1:
                aug[i] ^= aug[col]
    return from_rows([row >> d for row in aug], d)


def random_gl(d, rng):
    while True:
        x = rng.getrandbits(d * d)
        if rank2(x, d, d) == d:
            return x


def sandwich(fmt, terms, P, Q, S):
    """(U, V, W) -> (P U Q^-1, Q V S^-1, S W P^-1) with P in GL_n, Q in GL_m, S in GL_p."""
    n, m, p = fmt
    Pi, Qi, Si = inverse2(P, n), inverse2(Q, m), inverse2(S, p)
    return [(matmul2(matmul2(P, a, n, n, m), Qi, n, m, m),
             matmul2(matmul2(Q, b, m, m, p), Si, m, p, p),
             matmul2(matmul2(S, c, p, p, n), Pi, p, n, n)) for a, b, c in terms]


# ------------------------------------------------------------------------------------------ format maps
def map_c(fmt, terms):
    """c: (U, V, W) -> (V, W, U), format (n, m, p) -> (m, p, n); in the bit layout of gf2mm a pure relabelling."""
    n, m, p = fmt
    return (m, p, n), [(b, c, a) for a, b, c in terms]


def map_t(fmt, terms):
    """t: (U, V, W) -> (W^T, V^T, U^T), format (n, m, p) -> (n, p, m)."""
    n, m, p = fmt
    return (n, p, m), [(transpose(c, p, n), transpose(b, m, p), transpose(a, n, m)) for a, b, c in terms]


WORDS = ("id", "c", "cc", "t", "tc", "tcc")          # read left to right: "tc" = t, then c


def apply_word(word, fmt, terms):
    if word != "id":
        for letter in word:
            fmt, terms = (map_c if letter == "c" else map_t)(fmt, terms)
    return fmt, terms


def word_format(word, fmt):
    return apply_word(word, fmt, [])[0]


# ------------------------------------------------------------------------------------------ the invariant
def term_ranks(fmt, terms):
    n, m, p = fmt
    return [(rank2(a, n, m), rank2(b, m, p), rank2(c, p, n)) for a, b, c in terms]


def kappa(fmt, terms):
    """Multiset of per-term rank triples; for m = p != n the key (rk V, min(rk U, rk W), max(rk U, rk W))."""
    n, m, p = fmt
    rk = term_ranks(fmt, terms)
    if len({n, m, p}) == 3:
        keys = rk
    elif m == p and n != m:
        keys = [(rv, min(ru, rw), max(ru, rw)) for ru, rv, rw in rk]
    else:
        raise ValueError(f"format {fmt} not handled")
    return tuple(sorted(Counter(keys).items()))


def raw_multiset(fmt, terms):
    return tuple(sorted(Counter(term_ranks(fmt, terms)).items()))


def kappa_str(k):
    return "{" + ", ".join(f"({a},{b},{c}):{v}" for (a, b, c), v in k) + "}"


def canon_digest(terms):
    return hashlib.sha256(json.dumps(sorted(list(t) for t in terms)).encode()).hexdigest()


def both_verifiers(fmt, terms):
    WORK["verify"] += 1
    ok1 = gf2mm.verify(fmt, terms)
    WORK["verify_explicit"] += 1
    ok2 = gf2mm.verify_explicit(fmt, terms)
    return ok1, ok2


def verify_only(fmt, terms):
    WORK["verify"] += 1
    return gf2mm.verify(fmt, terms)


# ------------------------------------------------------------------------------------------ own schemes
def load_own():
    out = {}
    for fmt, (rank, count) in OWN.items():
        n, m, p = fmt
        files = sorted(SCHEME_DIR.glob(f"{n}x{m}x{p}_rank{rank}_*.json"))
        check(f"own <{n},{m},{p}>: {count} files", len(files) == count, f"{len(files)} found")
        lst = []
        for path in files:
            doc = json.loads(path.read_text(encoding="utf-8"))
            terms = [tuple(t) for t in doc["terms"]]
            keys_ok = set(doc) == {"format", "field", "rank", "convention", "terms", "products"}
            head_ok = (tuple(doc["format"]) == fmt and doc["field"] == "GF(2)" and doc["convention"] == gf2mm.CONVENTION
                       and doc["rank"] == len(terms) == rank)
            gf2mm.check_factor_ranges(fmt, terms)
            shape_ok = len(set(terms)) == rank and all(a and b and c for a, b, c in terms)
            ok1, ok2 = both_verifiers(fmt, terms)
            prod_ok = doc["products"] == [gf2mm.describe_term(fmt, t) for t in terms]
            check(f"{path.name}: keys, header, {rank} distinct terms without zero factor, verify, verify_explicit, "
                  "products strings", keys_ok and head_ok and shape_ok and ok1 and ok2 and prod_ok,
                  f"keys {keys_ok}, header {head_ok}, terms {shape_ok}, verify {ok1}, verify_explicit {ok2}, "
                  f"products {prod_ok}")
            lst.append((path.name, terms))
        out[fmt] = lst
    return out


# ------------------------------------------------------------------------------------------ public files
def obtain(url, sha, cache, download):
    name = url.rsplit("/", 1)[1]
    for p in (cache / hashlib.sha1(url.encode("utf-8")).hexdigest(), cache / name):
        if p.is_file():
            data = p.read_bytes()
            if hashlib.sha256(data).hexdigest() == sha:
                return data
    if not download:
        return None
    time.sleep(1.0)                                   # at most one request per second
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    WORK["downloads"] += 1
    (cache / hashlib.sha1(url.encode("utf-8")).hexdigest()).write_bytes(data)
    return data


def frac(q):
    if isinstance(q, float):
        if q != int(q):
            raise ValueError(f"non-integral float {q}")
        return Fraction(int(q))
    return Fraction(str(q))


def w_index(x, fmt, reading):
    """Flat index of the third factor: reading 'ki' keeps position x as W[k][i] (index k*n+i); reading 'ik'
    takes position x as the output entry (i, k), index i*p+k, i.e. W[k][i] with k*n+i."""
    n, m, p = fmt
    if reading == "ki":
        return x
    i, k = divmod(x, p)
    return k * n + i


def dense_readings(fmt, us, vs, ws):
    n, m, p = fmt
    out = []
    for reading in ("ki", "ik"):
        terms = []
        for u, v, w in zip(us, vs, ws):
            if len(u) != n * m or len(v) != m * p or len(w) != p * n:
                raise ValueError("factor length does not fit the format")
            U = {x: frac(q) for x, q in enumerate(u) if frac(q) != 0}
            V = {x: frac(q) for x, q in enumerate(v) if frac(q) != 0}
            W = {w_index(x, fmt, reading): frac(q) for x, q in enumerate(w) if frac(q) != 0}
            terms.append((U, V, W))
        out.append((reading, terms))
    return out


def expand_sparse(rows, fresh, base):
    """Rows of {index, value}: index < base is a variable, index >= base the fresh combination fresh[index-base]."""
    memo = {}

    def vec(ix):
        if ix < base:
            return {ix: Fraction(1)}
        f = ix - base
        if f not in memo:
            acc = Counter()
            for e in fresh[f]:
                for key, val in vec(e["index"]).items():
                    acc[key] += frac(e["value"]) * val
            memo[f] = {k: v for k, v in acc.items() if v}
        return memo[f]

    out = []
    for row in rows:
        acc = Counter()
        for e in row:
            for key, val in vec(e["index"]).items():
                acc[key] += frac(e["value"]) * val
        out.append({k: v for k, v in acc.items() if v})
    return out


def read_json(data, fmt):
    d = json.loads(data.decode("utf-8"))
    if tuple(d["n"]) != fmt:
        raise ValueError(f"format {d['n']} differs from the pin {fmt}")
    n, m, p = fmt
    R = d["m"]
    sparse = d["u"] and isinstance(d["u"][0], list) and d["u"][0] and isinstance(d["u"][0][0], dict)
    if not sparse:
        return dense_readings(fmt, d["u"], d["v"], d["w"]), R
    U = expand_sparse(d["u"], d.get("u_fresh", []), n * m)
    V = expand_sparse(d["v"], d.get("v_fresh", []), m * p)
    outs = expand_sparse(d["w"], d.get("w_fresh", []), R)          # one row per entry of C, over the products
    if len(U) != R or len(V) != R or len(outs) != n * p:
        raise ValueError("sparse file does not fit the format")
    out = []
    for reading in ("ki", "ik"):
        terms = []
        for t in range(R):
            W = {w_index(o, fmt, reading): row[t] for o, row in enumerate(outs) if row.get(t)}
            terms.append((U[t], V[t], W))
        out.append((reading, terms))
    return out, R


def read_mpl(data, fmt):
    """Maple TriadSet of Triad([Matrix(n,m,..), Matrix(m,p,..), Matrix(p,n,..)]); the file's own check line is
    A.B - sum tr(X^T A) tr(Y^T B) Z^T, so the p x n matrix Z is W[k][i] (one reading)."""
    text = data.decode("utf-8")
    n, m, p = fmt
    mats = re.findall(r"Matrix\((\d+),\s*(\d+),\s*(\[\[.*?\]\])\)", text[text.index("TriadSet("):], re.S)
    if len(mats) % 3:
        raise ValueError("matrices do not come in triples")
    terms = []
    for q in range(0, len(mats), 3):
        dims = [(int(r), int(c)) for r, c, _ in mats[q:q + 3]]
        if dims != [(n, m), (m, p), (p, n)]:
            raise ValueError(f"triad shapes {dims}")
        X, Y, Z = ([[Fraction(tok.strip()) for tok in row.split(",")] for row in re.findall(r"\[([^\[\]]*)\]", s)]
                   for _, _, s in mats[q:q + 3])
        terms.append(({i * m + j: X[i][j] for i in range(n) for j in range(m) if X[i][j]},
                      {j * p + k: Y[j][k] for j in range(m) for k in range(p) if Y[j][k]},
                      {k * n + i: Z[k][i] for k in range(p) for i in range(n) if Z[k][i]}))
    return [("ki", terms)], len(terms)


def read_mathematica(data, fmt):
    """Mathematica list {{U (n x m), V (m x p), W (p x n)}, ...}; only digits, braces, commas and signs are
    accepted, then the text is read with ast.literal_eval (no evaluation). The p x n block is W[k][i]."""
    text = data.decode("utf-8")
    if not re.fullmatch(r"[\s{}0-9,+-]*", text):
        raise ValueError("unexpected characters")
    n, m, p = fmt
    lst = ast.literal_eval(text.replace("{", "[").replace("}", "]"))
    terms = []
    for X, Y, Z in lst:
        if (len(X), len(X[0]), len(Y), len(Y[0]), len(Z), len(Z[0])) != (n, m, m, p, p, n):
            raise ValueError("block shapes")
        terms.append(({i * m + j: Fraction(X[i][j]) for i in range(n) for j in range(m) if X[i][j]},
                      {j * p + k: Fraction(Y[j][k]) for j in range(m) for k in range(p) if Y[j][k]},
                      {k * n + i: Fraction(Z[k][i]) for k in range(p) for i in range(n) if Z[k][i]}))
    return [("ki", terms)], len(terms)


TOKEN = re.compile(r"\s*([+-]?)\s*(?:(\d+(?:/\d+)?)\*)?([abc])(\d)(\d)")


def linear_form(part):
    s = part.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    pos, out, letter = 0, Counter(), None
    while pos < len(s):
        mt = TOKEN.match(s, pos)
        if not mt or mt.end() == pos:
            raise ValueError(f"cannot parse {part!r}")
        sign, coef, let, x, y = mt.groups()
        if letter not in (None, let):
            raise ValueError(f"mixed letters in {part!r}")
        letter = let
        q = Fraction(coef) if coef else Fraction(1)
        out[(int(x) - 1, int(y) - 1)] += -q if sign == "-" else q
        pos = mt.end()
    return letter, {k: v for k, v in out.items() if v}


def split_top(line):
    parts, depth, cur = [], 0, ""
    for ch in line:
        depth += (ch == "(") - (ch == ")")
        if ch == "*" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def read_exp(data, fmt):
    """Kauers-Moosbauer .exp: one product per line, (a-form)*(b-form)*(c-form); c read as c_ki or as c_ik."""
    n, m, p = fmt
    parsed = []
    for line in data.decode("utf-8").splitlines():
        line = line.strip().rstrip(";+ ")
        if not line:
            continue
        forms = dict(linear_form(part) for part in split_top(line))
        if set(forms) != {"a", "b", "c"}:
            raise ValueError(f"line without a, b and c: {line!r}")
        parsed.append(forms)
    out = []
    for reading in ("ki", "ik"):
        terms = []
        for f in parsed:
            if any(not (0 <= i < n and 0 <= j < m) for i, j in f["a"]) or \
                    any(not (0 <= j < m and 0 <= k < p) for j, k in f["b"]):
                raise ValueError("a or b index out of range")
            pairs = f["c"] if reading == "ki" else {(k, i): q for (i, k), q in f["c"].items()}
            if any(not (0 <= k < p and 0 <= i < n) for k, i in pairs):
                break                                   # this reading does not fit the format
            terms.append(({i * m + j: q for (i, j), q in f["a"].items()},
                          {j * p + k: q for (j, k), q in f["b"].items()},
                          {k * n + i: q for (k, i), q in pairs.items()}))
        else:
            out.append((reading, terms))
    return out, len(parsed)


def read_npz(data, member, fmt):
    """Static decoding of a numpy object array of three int64 C-order matrices (u, v, w), each (rows x R),
    from its pickle stream: the opcodes are listed with pickletools.genops and only literal arguments are read;
    nothing is unpickled. Accepted only if the stream has exactly this shape."""
    n, m, p = fmt
    raw = zipfile.ZipFile(io.BytesIO(data)).read(member)
    if raw[:6] != b"\x93NUMPY":
        raise ValueError("not an .npy member")
    hlen, start = (int.from_bytes(raw[8:10], "little"), 10) if raw[6] == 1 else (int.from_bytes(raw[8:12], "little"), 12)
    header = ast.literal_eval(raw[start:start + hlen].decode("latin1").strip())
    if header != {"descr": "|O", "fortran_order": False, "shape": (3,)}:
        raise ValueError(f"unexpected header {header}")
    ops = list(pickletools.genops(raw[start + hlen:]))
    allowed_globals = {"numpy.core.multiarray _reconstruct", "numpy ndarray", "numpy dtype"}
    for op, arg, _ in ops:
        if op.name in ("GLOBAL", "STACK_GLOBAL", "INST", "OBJ", "NEWOBJ", "NEWOBJ_EX", "EXT1", "EXT2", "EXT4"):
            if op.name != "GLOBAL" or arg not in allowed_globals:
                raise ValueError(f"unexpected opcode {op.name} {arg!r}")
    strings = [arg for op, arg, _ in ops if op.name == "BINUNICODE"]
    if "i8" not in strings or "<" not in strings:
        raise ValueError("payload dtype is not little-endian int64")
    blobs = []
    for idx, (op, arg, _) in enumerate(ops):
        if op.name in ("SHORT_BINBYTES", "BINBYTES", "BINBYTES8") and len(arg) > 8:
            k = idx - 1
            while ops[k][0].name != "TUPLE2":
                k -= 1
            rows, cols = ops[k - 2][1], ops[k - 1][1]
            if ops[idx - 1][0].name != "NEWFALSE" or len(arg) != 8 * rows * cols:
                raise ValueError("payload is not a C-order int64 matrix of the stated shape")
            blobs.append((rows, cols, [int.from_bytes(arg[8 * q:8 * q + 8], "little", signed=True)
                                       for q in range(rows * cols)]))
    if [(r, c) for r, c, _ in blobs] != [(n * m, blobs[0][1]), (m * p, blobs[0][1]), (p * n, blobs[0][1])]:
        raise ValueError(f"matrix shapes {[(r, c) for r, c, _ in blobs]}")
    R = blobs[0][1]
    (_, _, u), (_, _, v), (_, _, w) = blobs
    us = [[u[x * R + t] for x in range(n * m)] for t in range(R)]
    vs = [[v[x * R + t] for x in range(m * p)] for t in range(R)]
    ws = [[w[x * R + t] for x in range(p * n)] for t in range(R)]
    return dense_readings(fmt, us, vs, ws), R


def read_notebook(data, var, fmt):
    """AlphaEvolve results notebook: the code cell that assigns var = (np.array([...]), np.array([...]),
    np.array([...])), matrices (rows x R) of integral floats; read with ast.literal_eval (no evaluation)."""
    n, m, p = fmt
    nb = json.loads(data.decode("utf-8"))
    cells = ["".join(c.get("source", "")) for c in nb["cells"] if c.get("cell_type") == "code"]
    src = [s for s in cells if f"{var} = (np.array(" in s]
    if len(src) != 1:
        raise ValueError(f"{len(src)} cells assign {var}")
    seg = src[0][src[0].index(f"{var} = (np.array("):]
    arrays = re.findall(r"np\.array\((\[.*?\]\])", seg, re.S)[:3]
    mats = [ast.literal_eval(a) for a in arrays]
    R = len(mats[0][0])
    if [len(M) for M in mats] != [n * m, m * p, p * n] or any(len(row) != R for M in mats for row in M):
        raise ValueError("array shapes")
    us = [[mats[0][x][t] for x in range(n * m)] for t in range(R)]
    vs = [[mats[1][x][t] for x in range(m * p)] for t in range(R)]
    ws = [[mats[2][x][t] for x in range(p * n)] for t in range(R)]
    return dense_readings(fmt, us, vs, ws), R


def parse(entry, data):
    pid, tgt, url, sha, reader, fmt, extra, gf2_only = entry
    if reader == "json":
        return read_json(data, fmt)
    if reader == "mpl":
        return read_mpl(data, fmt)
    if reader == "mathematica":
        return read_mathematica(data, fmt)
    if reader == "exp":
        return read_exp(data, fmt)
    if reader == "npz":
        return read_npz(data, extra, fmt)
    if reader == "notebook":
        return read_notebook(data, extra, fmt)
    raise ValueError(reader)


def exact_valid(fmt, terms):
    """All Brent equations over Q: the tensor sum_t U_t (x) V_t (x) W_t equals T<n,m,p> exactly."""
    WORK["exact_tensor_builds"] += 1
    n, m, p = fmt
    acc = Counter()
    for U, V, W in terms:
        for a, x in U.items():
            for b, y in V.items():
                xy = x * y
                for c, z in W.items():
                    acc[(a, b, c)] += xy * z
    got = {key: v for key, v in acc.items() if v}
    want = {(i * m + j, j * p + k, k * n + i): 1 for i in range(n) for j in range(m) for k in range(p)}
    return got == want


def reduce2(terms):
    """Bitmask terms mod 2; None if a coefficient has an even denominator."""
    out = []
    for factors in terms:
        masks = []
        for X in factors:
            mask = 0
            for idx, q in X.items():
                if q.denominator % 2 == 0:
                    return None
                if q.numerator % 2:
                    mask |= 1 << idx
            masks.append(mask)
        out.append(tuple(masks))
    return out


def classify(entry, data):
    """Reading, GF(2) terms in the target format (all oriented images), invariant and canonical digest."""
    pid, tgt, url, sha, reader, fmt, extra, gf2_only = entry
    readings, R = parse(entry, data)
    WORK["files_parsed"] += 1
    WORK["readings_tried"] += len(readings)
    exact = [(lab, ts) for lab, ts in readings if exact_valid(fmt, ts)]
    info = {"exact_readings": [lab for lab, _ in exact], "rank": R}
    if gf2_only:
        mod2 = []
        for lab, ts in readings:
            red = reduce2(ts)
            if red is not None and verify_only(fmt, red):
                mod2.append((lab, ts))
        chosen = mod2
        info["how"] = "valid over GF(2) only"
    else:
        chosen = exact
        info["how"] = "valid exactly over Q"
    if len(chosen) != 1:
        return None, f"{len(chosen)} readings validate ({info['how']})", info
    reading, ts = chosen[0]
    red = reduce2(ts)
    if red is None:
        return None, "a denominator is even: no reduction mod 2", info
    info["denominators"] = sorted({q.denominator for t in ts for X in t for q in X.values()})
    if R != OWN[tgt][0]:
        return None, f"rank {R}, not {OWN[tgt][0]}", info
    if len(red) != R or len(set(red)) != R or not all(a and b and c for a, b, c in red):
        return None, "after reduction mod 2 some term is zero or repeated", info
    images = {}
    for word in WORDS:
        if word_format(word, fmt) == tgt:
            f2, ims = apply_word(word, fmt, red)
            ok1, ok2 = both_verifiers(f2, ims)
            if not (ok1 and ok2):
                return None, f"image under {word} fails a verifier", info
            images[word] = ims
    kappas = {kappa(tgt, ims) for ims in images.values()}
    if len(kappas) != 1:
        return None, "invariant depends on the orientation", info
    info.update(reading=reading, words=sorted(images), kappa=kappas.pop(),
                digest=min(canon_digest(ims) for ims in images.values())[:16])
    return info, "ok", info


# ------------------------------------------------------------------------------------------ checks
def format_maps(own):
    say("== format maps")
    rule_ok, tested = True, 0
    for n in range(1, 7):
        for m in range(1, 7):
            for p in range(1, 7):
                tested += 1
                fixing = [w for w in WORDS if word_format(w, (n, m, p)) == (n, m, p)]
                images = sorted(word_format(w, (n, m, p)) for w in WORDS)
                perms = sorted({(n, m, p), (n, p, m), (m, n, p), (m, p, n), (p, n, m), (p, m, n)})
                two_equal = len({n, m, p}) < 3
                rule_ok &= (len(fixing) > 1) == two_equal and sorted(set(images)) == perms
    check("the six words send (n,m,p) to its permutations, and a word other than id fixes (n,m,p) iff two of "
          "n, m, p are equal", rule_ok, f"{tested} formats with entries 1..6")
    fix256 = [w for w in WORDS if word_format(w, (2, 5, 6)) == (2, 5, 6)]
    fix355 = [w for w in WORDS if word_format(w, (3, 5, 5)) == (3, 5, 5)]
    check("words fixing (2,5,6): only id; words fixing (3,5,5): id and t", fix256 == ["id"] and fix355 == ["id", "t"],
          f"(2,5,6): {fix256}, (3,5,5): {fix355}")
    ok = True
    for fmt in ((2, 5, 6), (3, 5, 5)):
        std = gf2mm.standard_scheme(fmt)
        for w in WORDS:
            f2, ims = apply_word(w, fmt, std)
            ok &= all(both_verifiers(f2, ims))
            WORK["format_map_images"] += 1
    check("every word maps the standard algorithm of (2,5,6) and of (3,5,5) to a valid scheme of the image format "
          "(both verifiers)", ok, "12 images")
    ok = True
    count = 0
    for fmt, lst in own.items():
        for _, terms in lst:
            for w in WORDS:
                f2, ims = apply_word(w, fmt, terms)
                ok &= verify_only(f2, ims)
                count += 1
                WORK["format_map_images"] += 1
    check("every word maps each of the nine schemes to a valid scheme of the image format (verify)", ok,
          f"{count} images")


def group_checks(own, rng):
    say("== invariance of kappa under G")
    for fmt, lst in own.items():
        n, m, p = fmt
        bad = 0
        for _, terms in lst:
            k0 = kappa(fmt, terms)
            for _ in range(30):
                img = sandwich(fmt, terms, random_gl(n, rng), random_gl(m, rng), random_gl(p, rng))
                WORK["sandwich_images"] += 1
                if not verify_only(fmt, img) or kappa(fmt, img) != k0:
                    bad += 1
                if sorted(img) == sorted(terms):
                    WORK["sandwich_images_equal_to_input"] += 1
            if fmt == (3, 5, 5):
                f2, img = map_t(fmt, terms)
                ok1, ok2 = both_verifiers(f2, img)
                if f2 != fmt or not (ok1 and ok2) or kappa(f2, img) != k0:
                    bad += 1
        check(f"<{n},{m},{p}>: 30 random sandwiches per scheme" + (" and the self-map t" if fmt == (3, 5, 5) else "")
              + ": every image is valid and has the same kappa", bad == 0, f"{bad} failures")


def controls(own):
    say("== negative controls")
    fmt, terms = (2, 5, 6), own[(2, 5, 6)][0][1]
    a, b, c = terms[0]
    broken = [(a ^ 1, b, c)] + terms[1:]
    ok1, ok2 = both_verifiers(fmt, broken)
    check("control: a one-bit change in a scheme is rejected by both verifiers", not ok1 and not ok2,
          f"verify {ok1}, verify_explicit {ok2}")
    bad_images = 0
    for fmt in ((2, 5, 6), (3, 5, 5)):
        n, m, p = fmt
        P = from_rows([(1 << 0) | (1 << 1)] + [1 << i for i in range(1, n)], n)     # adds row 2 to row 1: P != I
        img = [(matmul2(P, a, n, n, m), b, c) for a, b, c in gf2mm.standard_scheme(fmt)]
        bad_images += not verify_only(fmt, img)
    check("control: U -> P U alone (P != I, no compensation) maps the standard algorithm to an invalid scheme",
          bad_images == 2, f"{bad_images} of 2 formats rejected")
    changed = sum(raw_multiset(*map_t((3, 5, 5), terms)) != raw_multiset((3, 5, 5), terms)
                  for _, terms in own[(3, 5, 5)])
    check("control: the unsymmetrised <3,5,5> multiset changes under t for some of the six schemes "
          "(the symmetrised key is needed)", changed > 0, f"{changed} of 6")


def coincidences(own_kappas, public_kappas):
    return [k for k in own_kappas if k in public_kappas]


def compare(own, public_rows, mode):
    for fmt, lst in own.items():
        n, m, p = fmt
        say(f"== <{n},{m},{p}>: public classes ({mode})")
        pub = [(pid, info) for pid, f, info in public_rows if f == fmt]
        classes = {}
        for pid, info in pub:
            classes.setdefault(info["kappa"], []).append((pid, info["digest"]))
        for q, (k, members) in enumerate(sorted(classes.items(), key=lambda kv: kv[1][0][0]), 1):
            digests = sorted({d for _, d in members})
            say(f"   class {q}: kappa {kappa_str(k)}")
            say(f"      {len(members)} representation(s): {' '.join(pid for pid, _ in members)}; "
                f"distinct GF(2) term sets: {len(digests)} ({' '.join(digests)})")
        n_sets = len({info["digest"] for _, info in pub})
        say(f"   {len(pub)} public representations, {len(classes)} distinct kappa, {n_sets} distinct GF(2) term sets")
        own_k = []
        for name, terms in lst:
            k = kappa(fmt, terms)
            own_k.append(k)
            say(f"   {name}: kappa {kappa_str(k)}")
        hits = coincidences(own_k, set(classes))
        check(f"<{n},{m},{p}>: no own kappa equals a public kappa ({mode})", not hits,
              f"{len(own_k)} own x {len(classes)} public classes, {len(hits)} coincidences")
        check(f"<{n},{m},{p}>: the {len(own_k)} own kappa are pairwise different", len(set(own_k)) == len(own_k),
              f"{len(set(own_k))} distinct")
        planted = coincidences(own_k, set(classes) | {own_k[0]})
        check(f"control <{n},{m},{p}>: with one own kappa planted among the public ones the comparison reports it",
              len(planted) == 1, f"{len(planted)} coincidence")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", help="directory (outside the repository) holding or receiving the pinned public files")
    ap.add_argument("--download", action="store_true", help="fetch pinned files missing from --cache")
    ap.add_argument("--print-recorded", action="store_true",
                    help="with --cache: also print the computed table in the form of RECORDED (checks are unchanged)")
    args = ap.parse_args(argv)
    if args.download and not args.cache:
        ap.error("--download needs --cache DIR")
    say("GF(2) schemes <2,5,6;47> x3 and <3,5,5;58> x6: verification, invariant, comparison with public schemes")
    own = load_own()
    format_maps(own)
    group_checks(own, random.Random(20261013))
    controls(own)

    public_rows = []
    if args.cache:
        cache = Path(args.cache).resolve()
        inside = cache == REPO or REPO in cache.parents
        check("cache directory lies outside the repository", not inside)
        if inside:
            return finish()
        cache.mkdir(parents=True, exist_ok=True)
        say("== public representations (pinned files, read from the cache)")
        computed = {}
        for entry in PUBLIC:
            pid, tgt, url, sha, reader, fmt, extra, gf2_only = entry
            data = obtain(url, sha, cache, args.download)
            if data is None:
                check(f"{pid}: a copy with the pinned SHA-256 is in the cache", False, url.rsplit("/", 1)[1])
                continue
            WORK["sha256_checks"] += 1
            got = hashlib.sha256(data).hexdigest()
            if not check(f"{pid}: SHA-256 equals the pin", got == sha, f"{url.rsplit('/', 1)[1]}"):
                continue
            info, status, raw = classify(entry, data)
            if info is None:
                check(f"{pid}: parsed, validated, reduced mod 2, oriented to <{tgt[0]},{tgt[1]},{tgt[2]}>", False,
                      status)
                continue
            rec = RECORDED.get(pid)
            same = rec == (info["reading"], kappa_str(info["kappa"]), info["digest"])
            check(f"{pid}: {info['how']} in exactly one reading of the third factor ({info['reading']}), reduced mod "
                  f"2 to {info['rank']} distinct non-zero terms, oriented by {'+'.join(info['words'])}, both "
                  "verifiers; kappa and term set equal the recorded ones", same,
                  f"published format {fmt}, rank {info['rank']}, denominators {info['denominators']}, "
                  f"digest {info['digest']}")
            computed[pid] = (info["reading"], kappa_str(info["kappa"]), info["digest"])
            public_rows.append((pid, tgt, info))
            if gf2_only:
                check(f"control {pid}: the GF(2)-only representation fails the exact validation over Q in both readings",
                      raw["exact_readings"] == [], f"exact readings {raw['exact_readings']}")
        first = PUBLIC[0]
        data = obtain(first[2], first[3], cache, False)
        if data is not None:
            corrupt = bytes([data[0] ^ 1]) + data[1:]
            check("control: a copy with one changed byte fails its SHA-256 pin",
                  hashlib.sha256(corrupt).hexdigest() != first[3])
        check("all 33 pinned representations were read and classified", len(public_rows) == len(PUBLIC),
              f"{len(public_rows)} of {len(PUBLIC)}")
        pins = {e[0]: e[3] for e in PUBLIC}
        for pid, url, sha, compression in ALIASES:
            data = obtain(url, sha, cache, args.download)
            ok = data is not None and hashlib.sha256(data).hexdigest() == sha
            if ok:
                WORK["sha256_checks"] += 1
                content = bz2.decompress(data) if compression == "bz2" else data
                ok = hashlib.sha256(content).hexdigest() == pins[pid]
            check(f"primary copy of {pid}: {url.split('/')[2]} .../{url.rsplit('/', 1)[1]} has its pinned SHA-256 and "
                  f"its content{' (decompressed)' if compression else ''} is byte-identical to {pid}", ok)
        if args.print_recorded:
            say("RECORDED = {")
            for pid in sorted(computed):
                say(f"    {pid!r}: {computed[pid]!r},")
            say("}")
        compare(own, public_rows, "computed from the pinned files")
    else:
        say("== public representations: RECORDED invariants (offline; run with --cache DIR to recompute them)")
        check("recorded table covers the 33 pinned representations", sorted(RECORDED) == sorted(e[0] for e in PUBLIC),
              f"{len(RECORDED)} recorded")
        for pid, tgt, *_ in PUBLIC:
            if pid in RECORDED:
                reading, kstr, digest = RECORDED[pid]
                k = tuple(sorted(((tuple(int(x) for x in key.split(",")), int(v))
                                  for key, v in re.findall(r"\((\d,\d,\d)\):(\d+)", kstr))))
                public_rows.append((pid, tgt, {"kappa": k, "digest": digest}))
        compare(own, public_rows, "recorded")
    return finish()


def finish():
    say()
    say("work: " + ", ".join(f"{k}={v}" for k, v in sorted(WORK.items())))
    if FAILURES:
        say(f"FAILED: {len(FAILURES)} check(s)")
        for f in FAILURES:
            say("   " + f)
        return 1
    say("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
