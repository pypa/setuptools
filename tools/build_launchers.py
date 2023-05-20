"""
Build executable launchers for Windows.

Build module requires installation of
`CMake <https://cmake.org/download/>`_ and Visual Studio.

Please ensure that buildtools v143 or later are installed for Visual
Studio. Ensure that you install ARM build tools.

From Visual Studio Installer:
Visual Studio -> Modify -> Individual Components

List of components needed to install to compile on ARM:
- C++ Universal Windows Platform Support for v143 build Tools (ARM64)
- MSVC v143 - VS 2022 C++ ARM64 build tools (latest)
- MSVC v143 - VS 2022 C++ ARM64 Spectre-mitigated libs (latest)
- C++ ATL for latest v143 build tools (ARM64)
"""

import os
import functools
import pathlib
import shutil
import subprocess


BUILD_TARGETS = ["cli", "gui"]
GUI = {"cli": 0, "gui": 1}
BUILD_PLATFORMS = ["Win32", "x64", "arm64"]
REPO_ROOT = pathlib.Path(__file__).parent.parent.resolve()
LAUNCHER_CMAKE_PROJECT = REPO_ROOT / "launcher"
MSBUILD_OUT_DIR = REPO_ROOT / "setuptools"
VISUAL_STUDIO_VERSION = "Visual Studio 17 2022"
"""
Version of Visual Studio that is currently installed on the machine.
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


def get_executable_name(name, platform: str):
    if platform in ["Win32", "x64"]:
        return f"{name}-{platform[-2:]}"
    return f"{name}-{platform}"


def generate_cmake_project(build_arena, cmake_project_path, platform, is_gui):
    subprocess.check_call(
        f'{get_cmake()} -G "{VISUAL_STUDIO_VERSION}" -A "{platform}"'
        f' {cmake_project_path} -DGUI={is_gui}',
        cwd=build_arena,
        shell=True,
    )


def build_cmake_project_with_msbuild(build_arena, msbuild_parameters):
    cmd = f"{get_msbuild()} launcher.vcxproj " + msbuild_parameters
    subprocess.check_call(cmd, cwd=build_arena, shell=True)


@functools.lru_cache()
def get_cmake():
    """Find CMake using registry."""
    import winreg

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Kitware\CMake") as key:
        root = pathlib.Path(winreg.QueryValueEx(key, "InstallDir")[0])
    return root / 'bin\\CMake.exe'


@functools.lru_cache()
def get_msbuild():
    """Use VSWhere to find MSBuild."""
    vswhere = pathlib.Path(
        os.environ['ProgramFiles(x86)'],
        'Microsoft Visual Studio',
        'Installer',
        'vswhere.exe',
    )
    cmd = [
        vswhere,
        '-latest',
        '-prerelease',
        '-products',
        '*',
        '-requires',
        'Microsoft.Component.MSBuild',
        '-find',
        r'MSBuild\**\Bin\MSBuild.exe',
    ]
    try:
        return subprocess.check_output(cmd, encoding='utf-8', text=True).strip()
    except subprocess.CalledProcessError:
        raise SystemExit("Unable to find MSBuild; check Visual Studio install")


def main():
    # check for executables early
    get_cmake()
    get_msbuild()

    build_arena = REPO_ROOT / "build-arena"
    for platform in BUILD_PLATFORMS:
        for target in BUILD_TARGETS:
            print(f"Building {target} for {platform}")
            if build_arena.exists():
                shutil.rmtree(build_arena)
            build_arena.mkdir()

            generate_cmake_project(
                build_arena, LAUNCHER_CMAKE_PROJECT, platform, GUI[target]
            )

            build_params = (
                f"/t:build "
                f"/property:Configuration=Release "
                f"/property:Platform={platform} "
                f'/p:OutDir="{MSBUILD_OUT_DIR.resolve()}" '
                f"/p:TargetName={get_executable_name(target, platform)}"
            )
            build_cmake_project_with_msbuild(build_arena, build_params)

    # copying win32 as default executables
    for target in BUILD_TARGETS:
        executable = MSBUILD_OUT_DIR / f"{get_executable_name(target, 'Win32')}.exe"
        destination_executable = MSBUILD_OUT_DIR / f"{target}.exe"
        shutil.copy(executable, destination_executable)


if __name__ == "__main__":
    main()
