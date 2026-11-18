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
- **Milestone 2: in progress.** KRNL386 boots kernel32, GDI and USER; calc works (12+3= shows 15,
  `tools/check_calc.sh`); Explorer is the shell (desktop, taskbar, Start menu, Start -> Run ->
  calc: `check_explorer.sh`, `check_run.sh`); Solitaire as the shell (`check_sol.sh`).
  `Setup.cmd` (tools/setup.ps1) builds it all from the CD. See the handoff at the end.

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

8. **068F was not a stack.** The fault in 1:6808 is `cmp es:[0], ax` (result unused) on
   the far pointer GetProcAddress16 (2:1BF9) returns for kernel32's ThunkConnect32:
   KRNL386 touches the segment so the CPU's #NP loads it. 068F is GDI seg 42 (thunk
   connection data), a load-on-call code segment on Win95 (flags 1D10; Win98 SE's,
   seg 43, is PRELOAD 1D50). KRNL386's own exception 0Bh handler (1:0B06 -> 0B3E)
   only does __GP recovery and the debugger. pcrecomp identity `w16_np` now loads a
   not-present code segment on first touch through KRNL386's own GetCodeHandle
   (KERNEL.93, 1:0626) in its (hExe : segment number) form (1:056A checks ds:0 for
   'NE'): a real load with relocations. (Running the linked image's bytes instead is
   wrong here: seg 42's relocations then name placeholder selectors, and kernel32's
   thunk 35 rejects 017F.)
9. kernel32 crashed in 0xBFF76AB0 on [0xBFFBC2B8] (the NLS tables): VWIN32 0Ch's
   NLS block is at +3C on Win95 (+44 there is an input, 0xBFFBB5D4); vxd32 per build.
10. Seeds (tools/w16_seeds.py): KERNEL 3:316A/316D/3170 (one routine's three
   overlapping entries, cl = 2/1/0); GDI 11:0EB5/0EBA/0EBF (the `call cs:[si+0EC4h]`
   init stubs, Win98 SE's 11:2C9E..); USER 28: the 50 handlers of `call cs:[bx+60Bh]`
   (28:1ADA), read from the file.
11. SHELL VxD dx=106h (USER 64:20F8, a profile setting handed down; Win98 SE's USER
   never calls it): no-op.
12. KRNL386 1:5C14 read the IVT (F000:FF53) as a thread: vxd32's `cur_task` (CurTDB
   on every machine hand-over) read the thread's TDB at THDB+14 (Win98 SE); Win95's
   is THDB+1C. Per build (`thread_tdb`).
13. Win95 kernel32's per-process thunk dispatcher (0xBFF71988, USER -> MPR) for a
   process the thunk data does not list yet does `push dword [0xBFFBC04C]; retf`: a
   far jump to KRNL386 3:2372 on the 16-bit caller's frame (its return is USER's
   `pop ds; retf`, not a 66 EA stub). identity runs it as a far jump (Win95 only).
14. Now: GDI and USER boot, MSGSRV32 becomes the first task (VWIN32 01, CurTDB 0AD6),
   USER32's threads thunk into USER, and **calc starts**: DISPLAY.ExtTextOut draws its
   menu bar ("Edit", "View", "Help"). No window is captured yet (hiddenrun: "no
   window"; W16_WINDOW=1 needed, see below).
15. USER 9:10C7 called far through F000:FF53 with ds 2634: GDI 1:8B46's frame popped a
   stale ds. ne_lift had split 1:8B53 `mov di, 1` at 8B55 (a branch target in data
   decoded as code) and fallen through mid-instruction, losing `push [bp+0Ch]`.
   Seed 1:8B53 plus a lifter fix (pcrecomp 97103d9: a last instruction that straddles
   the next start decodes on from its end). Win98 SE's relift is unchanged. Found with
   the new `W16_DSW=2634` and `W16_WW=1367:8B56` (W16_FN=1 for both).

Win98 SE regression: win98-recomp built against pcrecomp branch w95 (build-w95)
passes check_calc and check_explorer (pcrecomp 5c84840 and 97103d9). Its xcopy fails 1-3 runs in 30, on its own
build too: k32host's CreateProcessA eax race (step 9 above; win95's fix applies).

16. **KRNL386 1:AF9C was GDI returning past its caller.** GDI 1:8334 is near-called inside
   81A6's frame and, after its far calls, ends `pop ax; pop bx; jmp 82F4` (81A6's epilogue).
   ne_lift's pops-past walk stopped at calls, so 81DC's call site ran on after the guest had
   returned and 82F4 ran a second time on a foreign frame (ds 0A67): Local32Size on a garbage
   heap. The Local32 heap itself was fine (the failed ReAlloc before it was that frame too).
   pcrecomp 5cb875d: after a far call the depth is unknown, and a pop then a jmp out of the
   function still counts. Win98 SE's relift gains 23 such checks; its gates still pass.
17. **Appearance.** reginst.py reads Win95's INFs (setupc.inf [winbase]/[winapps], shell.inf
   [shell], timezone.inf): grey faces, navy caption, teal desktop, as Win98 SE's box did.
   check_calc's reference is cut from a Win95 render (out/w95calc_15.png, not committed).
18. **setup.ps1** (Setup.cmd, setup.sh): only `win95\` off the CD and only the main CAB set
   (win95_02..28). MINI.CAB and PRECOPY1/2.CAB are never extracted, so their Windows 3.1
   KRNL386/USER/GDI cannot overwrite the real ones (a 3.10 KRNL386 stops setup). A 7-Zip pass
   of the main set alone matches work/sys file for file (2341 files). calc, notepad and
   Explorer rebased (0x01000000/0x01100000/0x01400000); w16test lifts Explorer, notepad and
   comdlg32 too. startmenu.py reads setupc.inf's Notepad line (a ;comment after the quotes).
19. **Explorer as the shell** (W16_SHELL=explorer.exe) paints the desktop (My Computer,
   Recycle Bin) and the taskbar with no new fix. Once (1 run in ~10) it stopped on a far call
   miss into USER 4:1AF1; not seen since.
20. **The Start menu click called a hook at 000C.** Win95 USER calls KEYBOARD.Inquire with
   ds:0CC6 and keeps its global hook table from 0CCE (WH_MSGFILTER's slot at 0CCC). drv16
   wrote Win98's 8-byte KBINFO (NumFuncKeys 12 at +6): the menu loop's CallMsgFilter ran
   "hook" 000C, proc 0100:0000. Win95's KBINFO is 6 bytes (pcrecomp 7673614, behind
   native32_w9x_is_win95). Found with W16_WW (now any selector) on 0A66:0CCC. Start -> Run ->
   calc then works (check_run); the Start menu's side banner is drawn as noise (bitmap).
21. **Solitaire** as the shell deals and its clock runs (check_sol): w16_seeds gives SOL 4:1644
   and WINMINE 1:03EE as on Win98 SE.

22. **Double-click (My Computer opens, check_mycomp).** Three bugs in a row.
   a. USER's PeekMessage (seg 3 0BE1) calls KERNEL.447 (1:8030) for a Win32 queue; the machine
      is now handed over there on Win95 (identity w16_farcall, matched by the return offset 0BEF),
      so the input thread posts the second click while Explorer polls. The double-click itself
      is built in USER seg 3 1B9D..1C09 (deadline = time + [CA], hwnd, rect from [24C]/[24E]).
   b. That yield first stopped the boot: Win95's EnterCrst (kernel32 0xBFF7424F, KRNL386 1:7EDE)
      stores the *thread object* as a crst's owner, Win98 the TDBX. vwin32_crst_wake wrote the
      TDBX, so a woken thread re-entering its own Win16Mutex waited on itself. Same in
      vwin32_thread_done (calc's exit left the Win16Mutex held: Explorer froze after calc's X).
   c. "This file does not have a program associated": Win95's ShellExecute does RegQueryValue
      (Folder, "shell\open") and took 2 as no association. A key with no default value answers
      "" on Win9x; vxd32's VMM RegQueryValue does that now. reginst also makes
      Explorer\ShellExecuteHooks the guest's whole key (the host's URL hook read through).
   Win95 saves a folder's place in Explorer\Streams\0 and StreamMRU (the gates delete them).
23. **notepad** (check_notepad): Win95's comdlg32 thunk-connects to the 16-bit COMMDLG.DLL, which
   was not linked ("Error loading notepad.exe"). commdlg.new (setupc.inf installs it as
   COMMDLG.DLL) is now linked (relink.sh, setup.ps1), copied to SYSTEM (k32host) and its
   DLGTHKCONNECTIONDATALS dispatcher (3:01F2) seeded. Notepad's first wsprintf then needed
   USER 28:06DC's `jmp cs:[bx+147h]` table seeded (w16_seeds).
24. **winmine** (check_winmine): GDI CreatePen (1:565F) fell through `push 5689` into a code-map
   start at 5666 that `mov ax, [bp+0Ch]` (5665) straddles, losing `push ax`; its frame then
   popped the return offset as bp (bp 18F9 = the return address) and winmine's stack unwound
   past its top. ne_lift now decodes on past any straddled start that is not a known entry
   (export / far-call fixup): the CPU never lands inside an instruction. Win95 w16: GDI 1 and
   USER 28 change, plus two bogus streams; Win98 SE: see the regression note below.
25. **Start menu shortcuts did nothing** (check_startprog, check_close's Notepad): Win95's CShellLink
   LoadLibrarys LINKINFO.DLL before it reads a .lnk, and it was neither lifted nor in SYSTEM; the load
   failed quietly, so no link was read (generic icons) and the click ran nothing. Found with the new
   `W9X_DOSTRACE=1` (every int 21h with its path): 7143 C:\WINDOWS\LINKINFO.DLL along the search path
   on each click. linkinfo.dll is now in the w16test lift (setup.ps1) and k32host's SYSTEM copy list.
   startmenu.py's .lnk was fine. check_close's Notepad X is at 630,57 on Win95 (Win98's 614,35 missed).
26. **Start menu banner noise**: Explorer's bitmap 157 (21x130) is BI_RLE4; drv16's DeviceBitmapBits
   and DIBtoDevice read every DIB as BI_RGB. dib_unrle (pcrecomp drv16.c) unpacks RLE4/RLE8 first.

### Where milestone 2 stands (handoff)

All ten gates pass (work/gates_s26.txt): `check_m1`, `check_calc`, `check_explorer`, `check_run`,
`check_startprog`, `check_sol`, `check_mycomp`, `check_notepad`, `check_winmine`, `check_close`.
(tools/check_w16.sh, untracked, is Win98's chunk-1 test: its USER addresses are Win98 SE's; not a gate.)
Win98 SE regression: win98-recomp built against pcrecomp w95 (win98/build-w95, its w16 relinked with
this branch) passes check_calc and check_explorer. README has screenshots and a hero GIF (docs/img).

Run: `W16_LIBMAIN=KERNEL W16_WINDOW=1` (+ `W16_SHELL=explorer.exe`, `W16_INPUT=...`) through
tools/hiddenrun.py with an absolute exe path. Export PCRECOMP before build.cmd; a fresh
configure needs both build/CMakeCache.txt and build/build.ninja gone. Build all targets.
After a seed or lifter change: `sh work/relink.sh` (it links commdlg, winmine, sol and cards).
Debug: `W16_WW=sel:off`, `W16_FN=2` (every lifted 16-bit function with ss:sp bp: a bp that
equals a return offset is a lost push), `W9X_OPENTRACE=1` (LFN and 8.3 opens), `W9X_DOSTRACE=1`
(every int 21h, with its path), `W98_REGTRACE=1`, `W98_STACKS=secs`, w16test's `--firsthit LO HI`.

**Next:**
1. Explorer's rare far call miss into USER 4:1AF1 (step 19); not seen in this session's runs.
2. Beyond milestone 2: Control Panel, Find, Help (each a new DLL to lift), check_w16 ported to Win95's USER.
