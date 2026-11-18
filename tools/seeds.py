#!/usr/bin/env python3
"""Write the work/seeds/*.json the lift needs, from work/sys.

    py -3 tools/seeds.py

- kernel32: the byte after each `xchg [esp],eax; 66 CB` (o16 retf), where
  the host's ring-0 entries come back, and the KEXP header's two code
  entries (the boot entry, +0C, and +14), which no export reaches
  (survey.md, kernel32).
"""
import json, os, re, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'work')
SEEDS = os.path.join(W, 'seeds')


def main():
    import pefile
    os.makedirs(SEEDS, exist_ok=True)
    p = pefile.PE(os.path.join(W, 'sys', 'kernel32.dll'))
    b, img = p.OPTIONAL_HEADER.ImageBase, p.get_memory_mapped_image()
    k = [b + m.start() + 5 for m in re.finditer(rb'\x87\x04\x24\x66\xcb', img)]
    x = img.index(b'KEXP')
    kexp = struct.unpack_from('<6I', img, x + 4)
    k += [kexp[2], kexp[4]]
    open(os.path.join(SEEDS, 'kernel32.dll.json'), 'w').write(json.dumps(['0x%08X' % v for v in k]))
    print('kernel32: %d retf returns, boot entry %08X' % (len(k) - 2, kexp[2]), file=sys.stderr)


if __name__ == '__main__':
    main()
