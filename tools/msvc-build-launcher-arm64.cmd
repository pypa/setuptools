del -R build
mkdir build
cd build
call "cmake"
if ERRORLEVEL 1 (echo Cannot locate CMake on PATH & exit /b 2)
mkdir arm64
cd arm64
cmake -G "Visual Studio 17 2022" -A "arm64" ../../launcher
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=arm64 /p:OutDir="../../setuptools" /p:TargetName="cli-arm64" /p:GUI=0
MSBuild launcher.vcxproj /t:Build /property:Configuration=Release /property:Platform=arm64 /p:OutDir="../../setuptools" /p:TargetName="gui-arm64" /p:GUI=1

cd ..\..
