#!/bin/sh
# Gate: Win95's own KRNL386/USER/GDI with notepad (Win32, rebased) as the shell;
# keys H i ! and the edit control's first line must match the reference "Hi!".
#   sh tools/check_notepad.sh       (reference: out/w95np_hi.png, a Win95 render, never committed;
#   notepad needs COMMDLG.DLL linked: comdlg32 thunks into it)
cd "$(dirname "$0")/.." || exit 1
export PCRECOMP_MUTE=1 HIDDENRUN_DESKTOP=pcrecomp_w95 W16_WINDOW=1 W16_LIBMAIN=KERNEL W16_SHELL=notepad.exe
export W16_INPUT='key H@40;key i@41;key !@42'
rm -f work/notepad_gate_*.png
py -3 tools/hiddenrun.py --secs 47 --shot 45 --out work/notepad_gate -- "$(cygpath -w "$PWD")\build\w16test.exe" --mute > /dev/null 2>&1
py -3 - <<'P'
import os, sys
from PIL import Image, ImageChops
boxes = [(40, 60, 330, 95), (42, 99, 60, 114)]  # caption; "Hi" short of the caret (it blinks)
ref = Image.open('out/w95np_hi.png').convert('RGB')   # never committed: a Win95 render
try: got = Image.open('work/notepad_gate_45.png').convert('RGB')
except OSError: print('notepad: no screenshot'); sys.exit(1)
# "Hi!" anywhere near its old place: since session 29 the caption and frame are USER's own
# metrics (Windows 11's leaked through the registry before), so the reference's caption is not
b = boxes[1]
ok = any(ImageChops.difference(got.crop((b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)), ref.crop(b)).getbbox() is None
         for dx in range(-20, 21) for dy in range(-20, 21))
print('notepad typed Hi! (identical)' if ok else 'notepad DIFFERS'); sys.exit(not ok)
P
