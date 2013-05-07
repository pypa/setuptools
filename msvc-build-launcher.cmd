@echo off

REM VCVARSALL may be in Program Files or Program Files (x86)
REM Use old Visual Studio 2008 so created .exe will be compatible with
REM old Windows versions. Free express edition can be downloaded via:
REM http://download.microsoft.com/download/8/B/5/8B5804AD-4990-40D0-A6AA-CE894CBBB3DC/VS2008ExpressENUX1397868.iso
set PATH_OLD=%PATH%
set PATH=C:\Program Files\Microsoft Visual Studio 9.0\VC;%PATH%
set PATH=C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC;%PATH%

REM set up the environment to compile to x86
call VCVARSALL x86 >nul 2>&1
if "%ERRORLEVEL%"=="0" (
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /out:setuptools/cli-32.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x86 /out:setuptools/gui-32.exe
) else (
  echo Visual Studio ^(Express^) 2008 not found to build Windows 32-bit version
)

REM now for 64-bit
call VCVARSALL x86_amd64 >nul 2>&1
if "%ERRORLEVEL%"=="0" (
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /out:setuptools/cli-64.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:x64 /out:setuptools/gui-64.exe
) else (
  echo Visual Studio ^(Express^) 2008 not found to build Windows 64-bit version
)

REM Windows RT ARM build requires both freeware
REM "Visual Studio Express 2012 for Windows 8" and
REM "Visual Studio Express 2012 for Windows Desktop" to be installed from
REM http://www.microsoft.com/visualstudio/eng/products/visual-studio-express-products
set PATH=%PATH_OLD%
set PATH=C:\Program Files\Microsoft Visual Studio 11.0\VC;%PATH%
set PATH=C:\Program Files (x86)\Microsoft Visual Studio 11.0\VC;%PATH%
call VCVARSALL x86_arm >nul 2>&1
if "%ERRORLEVEL%"=="0" (
  echo Building Windows RT Version ...
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" /D _ARM_WINAPI_PARTITION_DESKTOP_SDK_AVAILABLE launcher.c /O2 /link /MACHINE:ARM /SUBSYSTEM:CONSOLE /out:setuptools/cli-arm-32.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" /D _ARM_WINAPI_PARTITION_DESKTOP_SDK_AVAILABLE launcher.c /O2 /link /MACHINE:ARM /SUBSYSTEM:WINDOWS /out:setuptools/gui-arm-32.exe
) else (
  echo Visual Studio ^(Express^) 2012 not found to build Windows RT Version
)

set PATH=%PATH_OLD%

