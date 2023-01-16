import shutil
from pathlib import Path
import subprocess

BUILD_TARGETS = ["cli", "gui"]
GUI = {"cli": 0, "gui": 1}
BUILD_PLATFORMS = ["Win32", "x64", "arm64"]
REPO_ROOT = Path(__file__).parent.parent.resolve()
LAUNCHER_CMAKE_PROJECT = REPO_ROOT / "launcher"
MSBUILD_OUT_DIR = REPO_ROOT / "setuptools"


def get_executable_name(name, platform: str):
    if platform in ["Win32", "x64"]:
        return f"{name}-{platform[-2:]}"
    return f"{name}-{platform}"


def generate_cmake_project(build_arena, cmake_project_path, platform):
    subprocess.check_call(f'cmake -G "Visual Studio 17 2022" -A "{platform}"'
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
