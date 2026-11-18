#!/usr/bin/env python3
"""Win98 SE -> Win95 kernel32: functions and VxD service ids, by call graph.

    py -3 tools/k32svc.py ../win98/work kernel32.dll work [--c]

Functions are paired by export name, then a paired function's direct callees
are paired in order when both call the same number of functions; the
service ids each pair pushes for VxDCall are paired the same way. Prints
`w98 -> w95 (votes)` for every id seen, a split vote as several. Needs both
catalogs (work/cat/kernel32.dll.functions.json, from tools/lift.py).
ponytail: positional, so a reordered body is skipped, never guessed.
"""
import collections, json, os, re, sys
import pefile


def side(work, name):
    p = pefile.PE(os.path.join(work, 'sys', name))
    base, img = p.OPTIONAL_HEADER.ImageBase, p.get_memory_mapped_image()
    ex = {e.name.decode(): base + e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
    vx = base + {e.ordinal: e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols}[1]
    cat = json.load(open(os.path.join(work, 'cat', name.lower() + '.functions.json')))['functions']
    fn = {f['address']: f for f in cat}
    svc = {}
    for a, f in fn.items():
        ids = []
        for m in re.finditer(rb'\x68(....)\xe8(....)', img[a - base:f['end'] - base], re.S):
            if a + m.start() + 10 + int.from_bytes(m.group(2), 'little', signed=True) == vx:
                ids.append(int.from_bytes(m.group(1), 'little'))
        svc[a] = ids
    return ex, fn, svc


def main():
    w98, name, w95 = sys.argv[1:4]
    ex98, fn98, sv98 = side(w98, name); ex95, fn95, sv95 = side(w95, name)
    pair = {ex98[n]: ex95[n] for n in ex98 if n in ex95 and ex98[n] in fn98 and ex95[n] in fn95}
    todo = list(pair.items())
    votes = collections.defaultdict(collections.Counter)
    while todo:
        a, b = todo.pop()
        s1, s2 = sv98[a], sv95[b]
        if len(s1) == len(s2):
            for x, y in zip(s1, s2): votes[x][y] += 1
        c1, c2 = fn98[a]['calls_to'], fn95[b]['calls_to']
        if len(c1) == len(c2):
            for x, y in zip(c1, c2):
                if x in fn98 and y in fn95 and x not in pair:
                    pair[x] = y; todo.append((x, y))
    print('# %d functions paired' % len(pair), file=sys.stderr)
    seen = sorted({i for s in sv98.values() for i in s})
    for i in seen:
        c = votes.get(i)
        print('%08X -> %s' % (i, ' '.join('%08X:%d' % kv for kv in c.most_common()) if c else '?'))
    if '--pairs' in sys.argv:
        for a in sorted(pair): print('F %08X %08X' % (a, pair[a]))




def why(w95id):
    """--why ID: the Win95 functions pushing ID, their Win98 pair and its ids."""
    ex98, fn98, sv98 = side(sys.argv[1], sys.argv[2]); ex95, fn95, sv95 = side(sys.argv[3], sys.argv[2])
    pair = {ex98[n]: ex95[n] for n in ex98 if n in ex95 and ex98[n] in fn98 and ex95[n] in fn95}
    todo = list(pair.items())
    while todo:
        a, b = todo.pop()
        c1, c2 = fn98[a]['calls_to'], fn95[b]['calls_to']
        if len(c1) == len(c2):
            for x, y in zip(c1, c2):
                if x in fn98 and y in fn95 and x not in pair: pair[x] = y; todo.append((x, y))
    inv = {v: k for k, v in pair.items()}
    n95 = {v: k for k, v in ex95.items()}
    for b, ids in sorted(sv95.items()):
        if w95id in ids:
            a = inv.get(b)
            print('w95 %08X %-24s %s | w98 %s %s' % (b, n95.get(b, ''), ' '.join('%08X' % i for i in ids),
                  '%08X' % a if a else '?', ' '.join('%08X' % i for i in sv98[a]) if a else ''))


if __name__ == "__main__":
    if "--why" in sys.argv: why(int(sys.argv[sys.argv.index("--why") + 1], 16))
    else: main()
