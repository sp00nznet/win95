#!/usr/bin/env python3
"""Name host addresses (a fault's eip, return addresses) from a build's PDB.

    py -3 tools/hostsym.py build/xcopy.exe 0x600F002C 0x6038C564 ...

The host is linked at a fixed base (/BASE:0x60000000, /DYNAMICBASE:NO for
xcopy), so the addresses a NATIVE32_DEBUG_CHILD run prints are the image's.
ponytail: 32-bit Python not needed, dbghelp's 64-bit API reads a 32-bit PDB.
"""
import ctypes, ctypes.wintypes as W, os, sys

dbg = ctypes.WinDLL('dbghelp')
class SYM(ctypes.Structure):
    _fields_ = [('SizeOfStruct', W.ULONG), ('TypeIndex', W.ULONG), ('Reserved', ctypes.c_uint64 * 2), ('Index', W.ULONG),
                ('Size', W.ULONG), ('ModBase', ctypes.c_uint64), ('Flags', W.ULONG), ('Value', ctypes.c_uint64),
                ('Address', ctypes.c_uint64), ('Register', W.ULONG), ('Scope', W.ULONG), ('Tag', W.ULONG),
                ('NameLen', W.ULONG), ('MaxNameLen', W.ULONG), ('Name', ctypes.c_char * 256)]
class LINE(ctypes.Structure):
    _fields_ = [('SizeOfStruct', W.DWORD), ('Key', ctypes.c_void_p), ('LineNumber', W.DWORD), ('FileName', ctypes.c_char_p), ('Address', ctypes.c_uint64)]

h = ctypes.c_void_p(0x1234)
dbg.SymSetOptions(0x10 | 0x2)   # LOAD_LINES | UNDNAME
dbg.SymInitialize(h, None, False)
exe = os.path.abspath(sys.argv[1])
dbg.SymLoadModuleEx.restype = ctypes.c_uint64
dbg.SymLoadModuleEx(h, None, exe.encode(), None, ctypes.c_uint64(0x60000000), 0x4000000, None, 0)
for a in sys.argv[2:]:
    va = int(a, 16); s = SYM(); s.SizeOfStruct = 88; s.MaxNameLen = 255; d = ctypes.c_uint64(); ln = LINE(); ln.SizeOfStruct = ctypes.sizeof(LINE); dd = W.DWORD()
    name = s.Name.decode() + '+0x%X' % d.value if dbg.SymFromAddr(h, ctypes.c_uint64(va), ctypes.byref(d), ctypes.byref(s)) else '?'
    where = '%s:%d' % (ln.FileName.decode(), ln.LineNumber) if dbg.SymGetLineFromAddr64(h, ctypes.c_uint64(va), ctypes.byref(dd), ctypes.byref(ln)) else ''
    print('%08X %s %s' % (va, name, where))
