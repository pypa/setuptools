@echo off

REM Build with jaraco/windows Docker image

set PATH_OLD=%PATH%
set PATH=C:\BuildTools\VC\Auxiliary\Build;%PATH_OLD%

REM now for arm 64-bit
REM Cross compile for arm64
call VCVARSx86_arm64
if "%ERRORLEVEL%"=="0" (
  cl /D "GUI=0" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:arm64 /SUBSYSTEM:CONSOLE /out:setuptools/cli-arm64.exe
  cl /D "GUI=1" /D "WIN32_LEAN_AND_MEAN" launcher.c /O2 /link /MACHINE:arm64 /SUBSYSTEM:WINDOWS /out:setuptools/gui-arm64.exe
) else (
  echo Visual Studio 2019 with arm64 toolchain not installed
)

set PATH=%PATH_OLD%

