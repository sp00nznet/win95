#!/usr/bin/env python3
"""Find Win95's counterpart of a Win98 SE kernel32 address, by masked bytes.

    py -3 tools/k32map.py ../win98/work/sys/kernel32.dll work/sys/kernel32.dll 0xBFFC9470 0xBFF8E9E1 d:0xBFF9AD46 ...

A code address: the bytes from it, with every kernel32 pointer and rel32
masked, searched for in the other kernel32. A data address: the bytes around
each instruction that names it, with the address itself masked; the dword
found there, by vote. ponytail: byte windows, not a function differ; a miss
or a split vote is reported, never guessed.
"""
import re, sys, collections
import pefile


def load(path):
    p = pefile.PE(path)
    return p.OPTIONAL_HEADER.ImageBase, p.get_memory_mapped_image()


def pattern(img, o, n, keep=None):
    """regex of img[o:o+n]: dwords whose top byte is BF and rel32s masked."""
    b = bytearray(img[o:o + n]); mask = [False] * n
    for i in range(n - 3):
        if b[i + 3] == 0xBF and b[i + 2] >= 0xF0 or (i and b[i - 1] in (0xE8, 0xE9) and i - 1 != keep):
            for j in range(4): mask[i + j] = True
    return b''.join(b'.' if m else re.escape(bytes([c])) for c, m in zip(b, mask))


def find_code(b98, i98, b95, i95, va):
    o = va - b98
    for n in (64, 48, 32, 24, 16):
        hits = [m.start() for m in re.finditer(pattern(i98, o, n), i95, re.S)]
        if len(hits) == 1:
            return b95 + hits[0], 'code/%d' % n
    return None, 'code: no unique match'


def find_data(b98, i98, b95, i95, va):
    key = va.to_bytes(4, 'little'); votes = collections.Counter()
    for m in re.finditer(re.escape(key), i98):
        o = m.start()
        for pre, post in ((12, 12), (8, 8), (6, 6)):
            if o < pre: continue
            p = pattern(i98, o - pre, pre) + b'(....)' + pattern(i98, o + 4, post)
            hits = list(re.finditer(p, i95, re.S))
            if len(hits) == 1:
                votes[int.from_bytes(hits[0].group(1), 'little')] += 1
                break
    if not votes: return None, 'data: no unique match'
    (v, n), *rest = votes.most_common()
    return v, 'data %d/%d refs' % (n, sum(votes.values()))


def main():
    if len(sys.argv) < 4: sys.exit(__doc__)
    b98, i98 = load(sys.argv[1]); b95, i95 = load(sys.argv[2])
    p98 = pefile.PE(sys.argv[1])
    code = [(p98.OPTIONAL_HEADER.ImageBase + s.VirtualAddress, s.Misc_VirtualSize) for s in p98.sections if s.Characteristics & 0x20]
    for a in sys.argv[3:]:
        va = int(a[2:] if a.startswith('d:') else a, 16)   # d:ADDR, a data slot inside a code section
        incode = not a.startswith('d:') and any(s <= va < s + n for s, n in code)
        r, how = (find_code if incode else find_data)(b98, i98, b95, i95, va)
        if r is None and incode: r, how = find_data(b98, i98, b95, i95, va)   # a code address named by others
        print('%08X -> %s  (%s)' % (va, '%08X' % r if r is not None else '????????', how))


if __name__ == '__main__':
    main()
