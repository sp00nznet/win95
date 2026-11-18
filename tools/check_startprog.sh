#!/bin/sh
# Gate: programs start from Explorer's Start menu (Programs > Accessories > ...): Notepad
# (shell32's context menu on the shortcut, then ShellExecute) and Solitaire (Games, a Win16 app).
#   sh tools/check_startprog.sh      (Windows 95 menu coordinates; Notepad is checked by its white client and a taskbar button)
cd "$(dirname "$0")/.." || exit 1
export PCRECOMP_MUTE=1 HIDDENRUN_DESKTOP=pcrecomp_w95 W16_WINDOW=1 W16_LIBMAIN=KERNEL W16_SHELL=Explorer.exe
MENU="click 29,587@20;click 92,356@23;click 220,351@26"
rm -f work/startprog_*.png
W16_INPUT="$MENU;click 322,394@29" py -3 tools/hiddenrun.py --secs 40 --shot 38 --out work/startprog_np -- "$(cygpath -w "$PWD")\build\w16test.exe" --mute > /dev/null 2>&1
W16_INPUT="$MENU;click 318,351@29;click 420,373@32" py -3 tools/hiddenrun.py --secs 57 --shot 55 --out work/startprog_sol -- "$(cygpath -w "$PWD")\build\w16test.exe" --mute > /dev/null 2>&1
py -3 - <<'P'
import sys
from PIL import Image, ImageChops
def shot(f):
    try: return Image.open(f).convert('RGB')
    except OSError: return None
np, sol = shot('work/startprog_np_38.png'), shot('work/startprog_sol_55.png')
# Notepad: a white edit area and a taskbar button (the caret blinks, so no exact reference)
np_ok = np is not None and np.getpixel((300, 300)) == (255, 255, 255) and     sum(1 for x in range(70, 400) for y in range(608, 628) if np.getpixel((x, y)) == (0, 0, 0)) > 150
# Solitaire's deal is seeded from the clock: count its felt (0,130,0) and the caption's blue
sol_ok = sol is not None and sum(1 for p in sol.crop((40, 320, 620, 460)).get_flattened_data() if p == (0, 130, 0)) > 50000 \
    and sol.getpixel((300, 65)) != (0, 128, 128)
print(f'startprog: notepad {np_ok}, solitaire {sol_ok}'); sys.exit(not (np_ok and sol_ok))
P
