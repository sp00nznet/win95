#!/bin/sh
# Milestone gate: boot Win95's own KRNL386/USER/GDI, MSGSRV32 starts calc,
# keys 1 2 + 3 = and the display region must match the reference "15.".
#   sh tools/check_calc.sh          (reference: work/calc_ref_15.png, cut from
#   out/w95calc_15.png on first use; never committed, it is a Win95 render)
cd "$(dirname "$0")/.." || exit 1
export PCRECOMP_MUTE=1 HIDDENRUN_DESKTOP=pcrecomp_w95 W16_WINDOW=1 W16_LIBMAIN=KERNEL
export W16_INPUT='key 1@40;key 2@41;key +@42;key 3@43;key =@44'
rm -f work/calc_gate_*.png
py -3 tools/hiddenrun.py --secs 52 --shot 50 --out work/calc_gate -- "$(cygpath -w "$PWD")\\build\\w16test.exe" --mute > /dev/null 2>&1
py -3 - <<'P'
import os, sys
from PIL import Image, ImageChops
box = (46, 116, 290, 138)                       # calc's display, in the shot
if not os.path.exists('work/calc_ref_15.png'):
    Image.open('out/w95calc_15.png').crop(box).save('work/calc_ref_15.png')
try: shot = Image.open('work/calc_gate_50.png').convert('RGB')
except OSError: print('calc: no screenshot'); sys.exit(1)
ref = Image.open('work/calc_ref_15.png').convert('RGB')
ok = any(ImageChops.difference(shot.crop((box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)), ref).getbbox() is None
         for dx in range(-20, 21) for dy in range(-20, 21))
print('calc 12+3= shows 15. (display identical)' if ok else 'calc display DIFFERS'); sys.exit(not ok)
P
