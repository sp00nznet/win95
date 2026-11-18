#!/bin/sh
# Gate: double-clicking My Computer opens and paints its folder window, then double-clicking
# (C:) lists work/root in a second window. Windows 95's coordinates and window sizes.
# (Win95: USER's PeekMessage hands the machine over at KERNEL.447 1:8030; the crst owner is the
# thread object; RegQueryValue of a key with no default answers "".)
cd "$(dirname "$0")/.." || exit 1
export PCRECOMP_MUTE=1 HIDDENRUN_DESKTOP=pcrecomp_w95 W16_WINDOW=1 W16_LIBMAIN=KERNEL W16_SHELL=Explorer.exe
rm -f work/mycomp_*.png
# the folders open at Explorer's default place (another run may have saved a moved one)
STREAMS='HKCU\Software\pcrecomp\w95\xcopy\HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Streams'
for n in 0 1 2 3 4 5; do MSYS2_ARG_CONV_EXCL='*' reg delete "$STREAMS\\$n" /f > /dev/null 2>&1; done
MSYS2_ARG_CONV_EXCL='*' reg delete "${STREAMS%Streams}StreamMRU" /f > /dev/null 2>&1
W16_INPUT="click 40,50@22;click 40,50@22.15;click 87,119@32;click 87,119@32.15" py -3 tools/hiddenrun.py --secs 46 --shot 30 --shot 45 --out work/mycomp -- "$(cygpath -w "$PWD")\build\w16test.exe" --mute > /dev/null 2>&1
py -3 - <<'P'
import sys
from PIL import Image
log = open('work/mycomp.log', errors='replace').read()
def look(t, box):
    try: im = Image.open(f'work/mycomp_{t}.png').convert('RGB')
    except OSError: return None
    x0, y0, x1, y1 = box
    n = lambda c: sum(1 for x in range(x0, x1) for y in range(y0, y1) if im.getpixel((x, y)) == c)
    tb = sum(1 for x in range(70, 400) for y in range(608, 628) if im.getpixel((x, y)) == (0, 0, 0))
    return n((255, 255, 255)), n((255, 255, 0)), n((0, 0, 0)), tb
fault = '=== fault' in log or 'unknown AX' in log
a, b = look(30, (56, 118, 258, 270)), look(45, (80, 140, 278, 292))
if not a or not b: print('mycomp: no screenshot'); sys.exit(1)
# My Computer: white client, (C:)/Control Panel/Printers (a little yellow), labels, a taskbar button;
# (C:): its folders (more yellow), labels, a second taskbar button
mc = a[0] > 20000 and 150 < a[1] < 800 and a[2] > 500 and a[3] > 150
c = b[0] > 20000 and b[1] > 800 and b[2] > 500 and b[3] > 250
print(f'mycomp: no fault {not fault}, My Computer painted {mc} {a}, C: listed {c} {b}')
sys.exit(fault or not mc or not c)
P
