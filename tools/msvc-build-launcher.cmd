del -R build
mkdir build
cd build
call "cmake"
if ERRORLEVEL 1 (echo Cannot locate CMake on PATH & exit /b 2)
mkdir win32
cd win32
cmake -G "Visual Studio 17 2022" -A "Win32" ../../launcher
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=Win32 /p:OutDir="../../setuptools" /p:TargetName="cli-32" /p:GUI=0
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=Win32 /p:OutDir="../../setuptools" /p:TargetName="gui-32" /p:GUI=1

cd ..
cd ..
REM buildout (and possibly other implementations) currently depend on
REM the 32-bit launcher scripts without the -32 in the filename, so copy them
REM there for now.
copy setuptools\cli-32.exe setuptools\cli.exe
copy setuptools\gui-32.exe setuptools\gui.exe

cd build
mkdir 64
cd 64
cmake -G "Visual Studio 17 2022" -A "x64" ../../launcher
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=x64 /p:OutDir="../../setuptools" /p:TargetName="cli-64" /p:GUI=0 
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=x64 /p:OutDir="../../setuptools" /p:TargetName="gui-64" /p:GUI=1

cd ..\..