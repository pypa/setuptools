@echo off

REM VCVARSALL may be in Program Files or Program Files (x86)
PATH=C:\Program Files\Microsoft Visual Studio 9.0\VC;%PATH%
PATH=C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC;%PATH%

REM set up the environment to compile to x86
call VCVARSALL x86
cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /out:setuptools/cli-32.exe
cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /out:setuptools/gui-32.exe

REM now for 64-bit
call VCVARSALL x86_amd64
cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /out:setuptools/cli-64.exe
cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /out:setuptools/gui-64.exe