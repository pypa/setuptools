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


def generate_cmake_project(build_arena, cmake_project_path, platform):
    subprocess.check_call(f'cmake -G "{VISUAL_STUDIO_VERSION}" -A "{platform}"'
                          f' {cmake_project_path}', shell=True, cwd=build_arena)


def build_cmake_project_with_msbuild(build_arena, msbuild_parameters):
    cmd = "MSBuild launcher.vcxproj " + msbuild_parameters
    subprocess.check_call(cmd, shell=True, cwd=build_arena)


def main():
    build_arena = REPO_ROOT / "build-arena"
    for platform in BUILD_PLATFORMS:
        if build_arena.exists():
            shutil.rmtree(build_arena)
        build_arena.mkdir()

        generate_cmake_project(build_arena, LAUNCHER_CMAKE_PROJECT.resolve(), platform)

        for target in BUILD_TARGETS:
            build_params = f"/t:build " \
                           f"/property:Configuration=Release " \
                           f"/property:Platform={platform} " \
                           f'/p:OutDir="{MSBUILD_OUT_DIR.resolve()}" ' \
                           f"/p:TargetName={get_executable_name(target, platform)} " \
                           f"/p:GUI={GUI[target]}"
            build_cmake_project_with_msbuild(build_arena, build_params)

    # copying win32 as default executables
    for target in BUILD_TARGETS:
        executable = MSBUILD_OUT_DIR / f"{get_executable_name(target, 'Win32')}.exe"
        destination_executable = MSBUILD_OUT_DIR / f"{target}.exe"
        shutil.copy(executable, destination_executable)


if __name__ == "__main__":
    main()
