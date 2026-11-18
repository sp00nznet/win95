# Windows 95 survey

Windows 95's userland on pcrecomp, measured against win98-recomp (Windows 98 SE),
which is done. `tools/survey.py work/sys/kernel32.dll` lists the kernel boundary;
`tools/k32map.py` and `tools/k32svc.py` pair Win95's kernel32 with Win98 SE's.

## Status

- **Source**: `W95_PLUS_AR.iso`, the only image in the source folder. Despite the
  name it is **English** (every resource is 0x409) **Windows 95 OSR2**: kernel32
  4.00.1111 ("950 B", 24 Aug 1996), user32/gdi32 4.00.950, Explorer 4.00.950 with
  IE 3's shdocvw. The ISO also carries Plus! and the CD extras; only `win95\` is
  used. No serial is needed or read.
- **Milestone 1: done.** `xcopy32 /?` on Windows 95's own lifted kernel32 prints
  exactly its string resources (4 + 27), `xcopy32 C:\TEST\SRC C:\TEST\DST /S /I`
  copies a tree byte-identically and `/P` honours scripted y/n/y
  (`tools/check_m1.sh`, three checks).
- **Milestone 2: started.** ne_link lifts Win95's KRNL386/GDI/USER/DDEML/MSGSRV32/SHELL/COMMCTRL
  in Win16 identity mode; KRNL386's own BootStrap opens and loads itself, runs GlobalInit and
  calls kernel32's boot entry, which runs; the boot then reaches ADVAPI32's entry (the first
  module beyond the xcopy lift). Next: the full lift (gdi32, advapi32, user32, mpr..., calc) and
  USER's LibEntry.

## The CD

| | Win95 OSR2 | Win98 SE |
|---|---|---|
| setup files | `win95\` : MINI.CAB, PRECOPY1/2.CAB, WIN95_02..28.CAB | `win98\` : BASE4.CAB, WIN98_xx.CAB |
| extract | `7z e` each CAB into `work\sys` (2341 files) | the same |
| xcopy | `xcopy32.exe` is the PE itself | `xcopy32.mod` (xcopy32.exe a stub) |
| NLS | unicode.nls, locale.nls, cp_*.nls | the same names |
| shell | Explorer 4.00.950, shell32 4.00.1111, IE 3 shdocvw, comctl32 4.70 | Explorer 4.72 (IE 4/5 integrated: browseui, shdoc401) |

## Load addresses

| module | Win95 | Win98 SE |
|---|---|---|
| kernel32 | 0xBFF70000, 0x68000, **no relocations** | 0xBFF70000, no relocations |
| user32 | 0xBFF60000 (44 KB) | 0xBFF50000 |
| gdi32 | 0xBFF30000 | 0xBFF20000 |
| explorer | 0x00400000 (rebase it, as on 98) | 0x00400000 |
| shell32 | 0x7FDC0000 | 0x7FCB0000 range |

## kernel32

Sections: `_FREQASM` 0xBFF71000, `.text` 0xBFF78000, `_INIT` 0xBFFBA000 (read-only
on 95, writable on 98), `.data` 0xBFFBC000. Same exit as Win98: ordinals 1-9
(VxDCall0..8) through the gate at **0xBFFBC004** (98: 0xBFFC9734); 502 VxDCall sites.

**KEXP header** (`_FREQASM`+0), the same layout as 98: `'KEXP'`, VWIN32's ring-0
table slot 0xBFFBC01A, 0xBFFBC278 (a pointer to the current thread pointer),
the **boot entry 0xBFFBB374** (98: 0xBFFC7AE4), 0, 0xBFF9647F. Neither boot entry
is reachable from an export: both are seeds (`work/seeds/kernel32.dll.json`).
pcrecomp picks the build by this boot entry (vxd32.c `k32()`).

**VWIN32's boot block** (0x9C bytes): field for field the same as Win98 SE's
(+08 PSP, +0C gate, +10/+14 LDT alias and base, +20..+2A the directories, +3C
KRNL386's block, +50..+58 the arena, +78/+7A). Win95's `_INIT` (0xBFFBA4C5) reads
exactly the offsets Win98's (0xBFFC6BD6) does.

**KRNL386's handshake block** differs (kernel32 0xBFF71408 checks it):

| | Win95 | Win98 SE |
|---|---|---|
| size (+0) | 0x60 | 0x54 |
| magic | +3C = 0x3406DD | +30 = 0x35AA69 |
| kernel32's id | +40 = [0xBFFBC448] (0x3C9C5B) | +34 = [0xBFFC9EC8] (the same value) |
| KRNL386 entries | +14..+34 (9), +48, +4C, +50, +5C | +14..+28 (6), +3C..+44, +50 |
| 16:16 data | +10, +54, +58 | +10, +48, +4C |
| kernel32 writes back | +04, +08, +0C, +44 | +04, +08, +0C, +38 |

**Addresses the host names**, Win98 SE -> Win95, found by `tools/k32map.py`
(masked bytes around the code, or around every reference to a data address, by
vote) and checked by hand:

| what | Win98 SE | Win95 |
|---|---|---|
| QT_Thunk (export) | 0xBFF727D9 | 0xBFF728D0 |
| FT_Prolog's patched target | 0xBFF7268D | 0xBFF72791 |
| ordinal 89 / 90 (thunk patchers) | 0xBFF725F0 / 0xBFF7273F | 0xBFF726F4 / 0xBFF72843 |
| _EnterSysLevel / _LeaveSysLevel (97/98) | 0xBFF741B4 / 0xBFF741ED | 0xBFF74230 / 0xBFF7426D |
| Win16Mutex pointer | 0xBFFC9470 | 0xBFFBF9E0 |
| kernel32's 32->16 thunk slot | 0xBFF9AD46 | 0xBFF979CA |
| USER32!UserSignalProc slot | 0xBFFC95C0 | 0xBFFBFB60 |
| Krn32Mutex (a crst) | 0xBFFC9D10 -> crst | 0xBFFBFA60 itself (see below) |
| console constructor | 0xBFF8E9E1 (0x470 bytes) | 0xBFF8C35E (0x478) |
| process's console field | PDB+B0 | PDB+AC |

## VxD services: what differs

`tools/k32svc.py ../win98/work kernel32.dll work` pairs 1122 functions by export
name and then by their callees in order, and pairs the service ids each pair
pushes. Most ids mean the same on both; the ones that do not are kernel32 doing
more itself on 95:

- **Krn32Mutex.** Win95's is a fixed crst at 0xBFFBFA60 (+4 recursion, +8 owner,
  +10 count, set up in `_INIT`), entered and left inline (0xBFF74398/0xBFF743D3).
  Contention is VWIN32 **4** (wait) and **5** (wake), with no argument; the woken
  waiter takes ownership itself. Win98 SE made it an ordinary crst (1D/1E).
- **Blocking calls release it.** kernel32 enters the Krn32Mutex just before
  VWIN32 2D (SleepEx, 0xBFF864B6) and the waits 2E/2F, and does not leave it
  after: ring 0 gives it up. 41 and 32 are called holding it and leave after.
- **Waits.** On 95 kernel32 keeps the objects' state: a sync object is {+0 type
  1 semaphore / 2 event / 3 mutex, +0C ring 0's waiter list, +10 count, +18
  event flags or mutex owner}; a process or thread (type > 4) has one at +0C.
  kernel32 tries the objects itself (0xBFF96882) and only then calls **2E**
  (sync object, ms, alertable) or **2F** (n, objects, ms, all, alertable); when
  it signals an object with waiters it calls **30** (object, flag). Win98 SE's
  5C/5D/30 mean something else (30 is DestroyWaitBlock there).
- **2A0021** on 95 is Win98's 64 (set thread priorities); same arguments.
- **A thread's block.** kernel32 frees thread+60 with VMM _HeapFree (0xBFF87632);
  Win98 SE hands its +58 to VWIN32 58.
- **The console.** ReadConsole waits on the console's sync object (2E) before
  VCOND 10; the console's input event is at +474 (98: +46C).

## Which win98 pieces apply as they are

| piece | on Win95 |
|---|---|
| lift (disasm32/drive32, LIFT32_W9X) | as is; 4076 kernel32 functions, 0 errors |
| vxd32.c gate, VMM memory, registry, VWIN32 threads, Int21Dispatch, VCOND | as is |
| vxd32.c Win98-only answers | behind `k32()` / `native32_w9x_is_win95()`: the table above |
| k32host.c | this repo's copy, with Win95's addresses and handshake block |
| regbox32 | as is, box `HKCU\Software\pcrecomp\w95\<app>` |
| Win16 identity, drv16, ne_link | ne_link as is (seeds per build); identity.c answers VWIN32 4.00 on 95 |

## Milestone 1 log

1. Boot entry not lifted: no export reaches `_INIT`; seeded from KEXP (+0C, +14).
2. kernel32's whole boot ran first time with Win95's addresses in k32host.
3. Unknown VWIN32 4: Win95's Krn32Mutex contention (above).
4. Deadlock: the service thread blocked in 2D holding the Krn32Mutex: the
   blocking calls release it (vxd32 `w95_krn32_drop` runs kernel32's own
   LeaveKrn32).
5. CreateProcess retried with mangled paths: Win98's wait found a Win95 object
   "already signalled"; Win95's waits are their own now.
6. Console constructor and PDB field found from Win98's agent entry (k32map).
7. Heap corruption (0xC0000374, seen by letting k32host's handler report it):
   VMM _HeapFree of the host's TDBX; the host's blocks are tracked and kept.
8. /P hung: the console wait; ready, as on 98.
9. 1 run in 20 died quietly. Two causes, found with `NATIVE32_DEBUG_CHILD`
   and `tools/hostsym.py` (a host address to its function and line):
   a TDBX's current-PSP pointer is at +40 on 95 (+50 on 98: 0xBFF76512 vs
   0xBFF76547), and k32host read CreateProcessA's eax after the machine lock
   was gone (another guest thread's eax; `guest_call` now holds it). The
   second race is in win98's k32host too. Soak: 40/40 copies, 8/8 gate runs.

## Milestone 2 log

1. **The CD's two KRNL386s.** `MINI.CAB` (and the PRECOPY CABs) hold Setup's own
   Windows 3.1-based mini Windows: KRNL386 "Kernel Interface Version 3.10" (75490 bytes,
   1995), USER, GDI, drivers, fonts, 13 names in all. Extracted after the main set
   they overwrite the real OSR2 files (KRNL386 126944 bytes, "Version 4.00"). Extract
   the main set (`win95_02.cab`, a spanned set of 02..28) last, or skip MINI/PRECOPY.
   The real USER.EXE/GDI.EXE export the thunk connections (USRTHKCONNECTIONDATALS seg
   30, MSGTHKCONNECTIONDATALS seg 28, GDITHKCONNECTIONDATALS seg 42, FT tables in
   29 and 43) as on 98: `tools/w16_seeds.py` finds them unchanged.
2. ne_link: link `kommctrl.dll` too (shell.new's COMMCTRL imports need its purges).
   101 segments, 1.2 MB image.
3. KRNL386 could not open itself: vxd32 read NATIVE32_W9X_ROOT with the CRT's
   `getenv`, which does not see what the host set with SetEnvironmentVariable in the
   same process; the first DOS call (before kernel32) went to a relative `root`.
   Now GetEnvironmentVariable (pcrecomp; Win98 SE gets it too).
4. kernel32 enters KRNL386 at **1:653A** (its 32->16 entry, through the table at
   KEXP+4; Win98 SE's 1:6582): a hand seed in w16_seeds.py.
5. QT_Thunk's tails for w16test's stubs: 0xBFF72964 and 0xBFF72A0A (Win98 SE's +F7
   inside QT_Thunk, instruction for instruction), kept at [0xBFFBC07C]/[0xBFFBC084],
   handshake +2C/+34 (98: +1C/+24).
6. Win95's calc.exe is linked at 0x400000 (98 SE's at 0x01000000), where the host's
   own EXE is: rebased to 0x01000000 (`work/rebased/calc_1000.exe`).
7. With the full lift (gdi32, advapi32, user32, mpr, calc, comctl32, shell32: 14025
   functions) ADVAPI32's and GDI32's entries run; kernel32's first QT_Thunk into
   KRNL386 (from 0xBFF97C32, landing in 1:6808) faults reading a bad flat address
   (01000001) through a selector. **Next**: that thunk's 16-bit frame (QT_Thunk
   0xBFF728D0 builds it from the thread's 16-bit stack, TIB+0E on 98), then GDI.EXE
   and USER.EXE's LibEntry, then calc as the shell, then Explorer.
   (Rebuild note: delete build/CMakeCache.txt after the first w16test lift: CMake
   picks the xcopy fallback at configure time.)

Win98 SE regression: win98-recomp built against pcrecomp branch w95 (build-w95)
passes check_calc and check_explorer. Its xcopy fails 1-3 runs in 30, on its own
build too: k32host's CreateProcessA eax race (step 9 above; win95's fix applies).

### Where milestone 2 stands (handoff)

kernel32's first thunk into KRNL386 (from 0xBFF97C32 through the handshake entry at
[0xBFFBC450], via QT_Thunk 0xBFF728D0) reaches 1:6808, whose first stack read goes
through **not-present selector 068F** (`[w16] not-present selector 068F read:
segment 0`, then a fault at flat 01000001). QT_Thunk's Win32-thread path takes ss
from TIB+7C and -base from TIB+78 (0xBFF7250F builds that alias from the thread's
stack bounds, TIB-10h+14/+18; the same code as Win98's 0xBFF7240B path), so 068F is
most likely that alias with its descriptor never made present. To find: who
allocates 068F (VWIN32 ring-0 +28 hands out bare selectors; kernel32 then writes
the descriptor through the LDT alias) and why Win95's write differs; `W95_LDTW=068F`
(k32host) logs every write to that descriptor with the C stack.
