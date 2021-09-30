@echo off

REM Use old Windows SDK 6.1 so created .exe will be compatible with
REM old Windows versions.
REM Windows SDK 6.1 may be downloaded at:
REM  http://www.microsoft.com/en-us/download/details.aspx?id=11310
set PATH_OLD=%PATH%

REM The SDK creates a false install of Visual Studio at one of these locations
set PATH=C:\Program Files\Microsoft Visual Studio 9.0\VC\bin;%PATH%
set PATH=C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin;%PATH%

REM set up the environment to compile to x86
call VCVARS32
if "%ERRORLEVEL%"=="0" (
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /SUBSYSTEM:CONSOLE /out:setuptools/cli-32.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /SUBSYSTEM:WINDOWS /out:setuptools/gui-32.exe
) else (
  echo Windows SDK 6.1 not found to build Windows 32-bit version
)

REM buildout (and possibly other implementations) currently depend on
REM the 32-bit launcher scripts without the -32 in the filename, so copy them
REM there for now.
copy setuptools/cli-32.exe setuptools/cli.exe
copy setuptools/gui-32.exe setuptools/gui.exe

REM now for 64-bit
REM Use the x86_amd64 profile, which is the 32-bit cross compiler for amd64
call VCVARSx86_amd64
if "%ERRORLEVEL%"=="0" (
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /SUBSYSTEM:CONSOLE /out:setuptools/cli-64.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /SUBSYSTEM:WINDOWS /out:setuptools/gui-64.exe
) else (
  echo Windows SDK 6.1 not found to build Windows 64-bit version
)

set PATH=%PATH_OLD%

