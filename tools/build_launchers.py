"""
Build module requires installation of CMake and Visual Studio. Please download and
install console CMake and ensure that you add it to your PATH.
You can find the latest CMake release at https://cmake.org/download/.

Please ensure that 143 buildtools are installed for Visual Studio. Ensure that you
install ARM build tools.

From visual studio installer:
Visual Studio -> Modify -> Individual Components

List of components to install to compile ARM:
C++ Universal Windows Platform Support for v143 build Tools (ARM64)
MSVC v143 - VS 2022 C++ ARM64 build tools (latest)
MSVC v143 - VS 2022 C++ ARM64 Spectre-mitigated libs (latest)
C++ ATL for latest v143 build tools (ARM64)
"""
import shutil
from pathlib import Path
import subprocess

BUILD_TARGETS = ["cli", "gui"]
GUI = {"cli": 0, "gui": 1}
BUILD_PLATFORMS = ["Win32", "x64", "arm64"]
REPO_ROOT = Path(__file__).parent.parent.resolve()
LAUNCHER_CMAKE_PROJECT = REPO_ROOT / "launcher"
MSBUILD_OUT_DIR = REPO_ROOT / "setuptools"
"""
Might be modified to visual studio that currently installed on the machine.
Not tested with the older visual studios less then 16 version.
Generators
* Visual Studio 17 2022        = Generates Visual Studio 2022 project files.
                                 Use -A option to specify architecture.
  Visual Studio 16 2019        = Generates Visual Studio 2019 project files.
                                 Use -A option to specify architecture.
  Visual Studio 15 2017 [arch] = Generates Visual Studio 2017 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 14 2015 [arch] = Generates Visual Studio 2015 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 12 2013 [arch] = Generates Visual Studio 2013 project files.
                                 Optional [arch] can be "Win64" or "ARM".
  Visual Studio 11 2012 [arch] = Deprecated.  Generates Visual Studio 2012
                                 project files.  Optional [arch] can be
                                 "Win64" or "ARM".
  Visual Studio 9 2008 [arch]  = Generates Visual Studio 2008 project files.
                                 Optional [arch] can be "Win64" or "IA64".
"""
VISUAL_STUDIO_VERSION = "Visual Studio 17 2022"


def get_executable_name(name, platform: str):
    if platform in ["Win32", "x64"]:
        return f"{name}-{platform[-2:]}"
    return f"{name}-{platform}"


def generate_cmake_project(cmake, build_arena, cmake_project_path, platform, is_gui):
    subprocess.check_call(f'{cmake} -G "{VISUAL_STUDIO_VERSION}" -A "{platform}"'
                          f' {cmake_project_path} -DGUI={is_gui}', cwd=build_arena, shell=True)


def build_cmake_project_with_msbuild(msbuild, build_arena, msbuild_parameters):
    cmd = f"{msbuild} launcher.vcxproj " + msbuild_parameters
    subprocess.check_call(cmd, cwd=build_arena, shell=True)


def get_cmake():
    try:
        subprocess.check_call("cmake", shell=True)
        return "cmake"
    except Exception:
        print("CMake is not found in your system PATH. Please install it from"
              " https://cmake.org/download/ and ensure that cmake added to path")
    print("Trying to locate cmake at default place")
    try:
        possible_cmake_location = '"C:\\Program Files\\CMake\\bin\\cmake.exe"'
        subprocess.check_call(possible_cmake_location)
        return possible_cmake_location
    except Exception:
        raise "Can't find CMake either in PATH and installed in programs files"


def get_msbuild():
    try:
        subprocess.check_call("MSBuild --help", shell=True)
        return "MSBuild"
    except Exception:
        print("MSBuild is not found in your path. Ensure that Visual Studio "
              "is installed")
    print("Trying work around to find MSBuild")
    try:
        # cmdlet that finds MSBuild
        msbuild_path = subprocess.check_output(
            '"%ProgramFiles(x86)%\\Microsoft Visual Studio'
            '\\Installer\\vswhere.exe" -latest -prerelease '
            '-products * -requires Microsoft.Component.'
            'MSBuild -find MSBuild\\**\\Bin\\MSBuild.exe',
            shell=True, encoding="utf-8").strip()
        if msbuild_path == "":
            raise
    except Exception:
        raise Exception("Ensure that Visual Studio is installed correctly")


def main():
    cmake = get_cmake()
    msbuild = f'"{get_msbuild()}"'

    build_arena = REPO_ROOT / "build-arena"
    for platform in BUILD_PLATFORMS:
        for target in BUILD_TARGETS:
            print(f"Building {target} for {platform}")
            if build_arena.exists():
                shutil.rmtree(build_arena)
            build_arena.mkdir()

            generate_cmake_project(cmake,
                                   build_arena,
                                   LAUNCHER_CMAKE_PROJECT,
                                   platform,
                                   GUI[target])

            build_params = f"/t:build " \
                           f"/property:Configuration=Release " \
                           f"/property:Platform={platform} " \
                           f'/p:OutDir="{MSBUILD_OUT_DIR.resolve()}" ' \
                           f"/p:TargetName={get_executable_name(target, platform)}"
            build_cmake_project_with_msbuild(msbuild, build_arena, build_params)

    # copying win32 as default executables
    for target in BUILD_TARGETS:
        executable = MSBUILD_OUT_DIR / f"{get_executable_name(target, 'Win32')}.exe"
        destination_executable = MSBUILD_OUT_DIR / f"{target}.exe"
        shutil.copy(executable, destination_executable)


if __name__ == "__main__":
    main()
