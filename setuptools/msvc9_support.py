"""
This module improve support for Microsoft Visual C++ compilers. (Windows Only)
"""
import os
import itertools
import distutils.errors

try:
    # Distutil file for MSVC++ 9.0 and upper
    import distutils.msvc9compiler as msvc9compiler
except ImportError:
    pass

try:
    # Distutil file for MSVC++ 14.0 and upper
    import distutils._msvccompiler as msvc14compiler
except ImportError:
    pass


import six

unpatched = dict()


def patch_for_specialized_compiler():
    """
    Patch functions in distutils to use standalone Microsoft Visual C++
    compilers.

    Known supported compilers:
    --------------------------
        Microsoft Visual C++ 9.0:
            Microsoft Visual C++ Compiler for Python 2.7 (x86, amd64);
            Microsoft Windows SDK 7.0 (x86, x64, ia64);
            Microsoft Windows SDK 6.1 (x86, x64, ia64)

        Microsoft Visual C++ 10.0:
            Microsoft Windows SDK 7.1 (x86, x64, ia64)

        Microsoft Visual C++ 14.0:
            Microsoft Visual C++ Build Tools 2015 (x86, x64, arm)
    """
    if 'distutils' not in globals():
        # The module isn't available to be patched
        return

    if unpatched:
        # Already patched
        return

    try:
        # Patch distutils.msvc9compiler
        unpatched['msvc9_find_vcvarsall'] = msvc9compiler.find_vcvarsall
        msvc9compiler.find_vcvarsall = msvc9_find_vcvarsall
        unpatched['msvc9_query_vcvarsall'] = msvc9compiler.query_vcvarsall
        msvc9compiler.query_vcvarsall = msvc9_query_vcvarsall
    except:
        pass

    try:
        # Patch distutils._msvccompiler._get_vc_env
        unpatched['msv14_get_vc_env'] = msvc14compiler._get_vc_env
        msvc14compiler._get_vc_env = msvc14_get_vc_env
    except:
        pass


def msvc9_find_vcvarsall(version):
    """
    Patched "distutils.msvc9compiler.find_vcvarsall" to use the standalone
    compiler build for Python (VCForPython). Fall back to original behavior
    when the standalone compiler is not available.

    Known supported compilers
    -------------------------
        Microsoft Visual C++ 9.0:
            Microsoft Visual C++ Compiler for Python 2.7 (x86, amd64)

    Parameters
    ----------
    version: float
        Required Microsoft Visual C++ version.

    Return
    ------
    vcvarsall.bat path: str
    """
    Reg = msvc9compiler.Reg
    VC_BASE = r'Software\%sMicrosoft\DevDiv\VCForPython\%0.1f'
    key = VC_BASE % ('', version)
    try:
        # Per-user installs register the compiler path here
        productdir = Reg.get_value(key, "installdir")
    except KeyError:
        try:
            # All-user installs on a 64-bit system register here
            key = VC_BASE % ('Wow6432Node\\', version)
            productdir = Reg.get_value(key, "installdir")
        except KeyError:
            productdir = None

    if productdir:
        vcvarsall = os.path.os.path.join(productdir, "vcvarsall.bat")
        if os.path.isfile(vcvarsall):
            return vcvarsall

    return unpatched['msvc9_find_vcvarsall'](version)


def msvc9_query_vcvarsall(ver, arch='x86', *args, **kwargs):
    """
    Patched "distutils.msvc9compiler.query_vcvarsall" for support standalones
    compilers.

    Known supported compilers
    -------------------------
        Microsoft Visual C++ 9.0:
            Microsoft Visual C++ Compiler for Python 2.7 (x86, amd64);
            Microsoft Windows SDK 7.0 (x86, x64, ia64);
            Microsoft Windows SDK 6.1 (x86, x64, ia64)

        Microsoft Visual C++ 10.0:
            Microsoft Windows SDK 7.1 (x86, x64, ia64)

    Parameters
    ----------
    ver: float
        Required Microsoft Visual C++ version.
    arch: str
        Target architecture.

    Return
    ------
    environment: dict
    """
    # Try to get environement from vcvarsall.bat (Classical way)
    try:
        return unpatched['msvc9_query_vcvarsall'](ver, arch, *args, **kwargs)
    except distutils.errors.DistutilsPlatformError:
        # Error if Vcvarsall.bat is missing
        pass
    except ValueError:
        # Error if environment not set after executing vcvarsall.bat
        pass

    # If vcvarsall.bat fail, try to set environment directly
    try:
        return _compute_env(ver, arch)
    except distutils.errors.DistutilsPlatformError as exc:
        _augment_exception(exc, ver, arch)
        raise


def msvc14_get_vc_env(plat_spec):
    """
    Patched "distutils._msvccompiler._get_vc_env" for support standalones
    compilers.

    Known supported compilers
    -------------------------
        Microsoft Visual C++ 14.0:
            Microsoft Visual C++ Build Tools 2015 (x86, x64, arm)

    Parameters
    ----------
    plat_spec: str
        Target architecture.

    Return
    ------
    environment: dict
    """
    try:
        return unpatched['msv14_get_vc_env'](plat_spec)
    except distutils.errors.DistutilsPlatformError:
        # Error if Vcvarsall.bat is missing
        pass

    # If vcvarsall.bat fail, try to set environment directly
    try:
        return _compute_env(version, plat_spec)
    except distutils.errors.DistutilsPlatformError as exc:
        _augment_exception(exc, version, plat_spec)
        raise


def _augment_exception(exc, version, arch):
    """
    Add details to the exception message to help guide the user
    as to what action will resolve it.
    """
    # Error if MSVC++ directory not found or environment not set
    message = exc.args[0]

    if "vcvarsall.bat" in message:
        # Special error message if MSVC++ not installed
        message = 'Microsoft Visual C++ %0.1f is required (%s).' %\
            (version, message)
        if int(version) == 9:
            if arch.lower().find('ia64') > -1:
                # For VC++ 9.0, if IA64 support is needed, redirect user
                # to Windows SDK 7.0
                message += ' Get it with "Microsoft Windows SDK 7.0": '
                message += r'www.microsoft.com/download/details.aspx?id=3138'
            else:
                # For VC++ 9.0 redirect user to Vc++ for Python 2.7 :
                # This redirection link is maintained by Microsoft.
                # Contact vspython@microsoft.com if it needs updating.
                message += r' Get it from http://aka.ms/vcpython27'
        elif int(version) == 10:
            # For VC++ 10.0 Redirect user to Windows SDK 7.1
            message += ' Get it with "Microsoft Windows SDK 7.1": '
            message += r'www.microsoft.com/download/details.aspx?id=8279'

    exc.args[0] = message


class PlatformInfo:
    """
    Find architecture informations and system paths.

    Parameters
    ----------
    arch: str
        Target architecture.
    """
    current_cpu = os.environ['processor_architecture'].lower()
    win_dir = os.environ['WinDir']
    program_files = os.environ['ProgramFiles']
    program_files_x86 = os.environ.get('ProgramFiles(x86)', program_files)

    def __init__(self, arch):
        self.arch = arch.lower()

    @property
    def target_cpu(self):
        return self.arch[self.arch.find('_') + 1:]

    def target_is_x86(self):
        return self.target_cpu == 'x86'

    def current_is_x86(self):
        return self.current_cpu != 'x86'

    def ccpu_dir(self, hidex86=False, x64=False):
        """
        Current platform specific subfolder.

        Parameters
        ----------
        hidex86: bool
            return '' and not '\x86' if architecture is x86.
        x64: bool
            return '\x64' and not '\amd64' if architecture is amd64.

        Return
        ------
        subfolder: str (starting with'\')
        """
        return (
            '' if (self.current_cpu == 'x86' and hidex86) else
            r'\x64' if (self.current_cpu == 'amd64' and x64) else
            r'\%s' % self.current_cpu
        )

    def tcpu_dir(self, hidex86=False, x64=False):
        """
        Target platform specific subfolder.

        Parameters
        ----------
        hidex86: bool
            return '' and not '\x86' if architecture is x86.
        x64: bool
            return '\x64' and not '\amd64' if architecture is amd64.

        Return
        ------
        subfolder: str (starting with'\')
        """
        return (
            '' if (self.target_cpu == 'x86' and hidex86) else
            r'\x64' if (self.target_cpu == 'amd64' and x64) else
            r'\%s' % self.target_cpu
        )

    def tools_extra(self, forcex86=False):
        """
        Platform specific subfolder for Visual C++ Tools.

        Parameters
        ----------
        forcex86: bool
            If cross compilation, return 'x86' as current architecture even
            if current acritecture is not x86.

        Return
        ------
        subfolder: str (starting with'\')
        """
        path = self.tcpu_dir(True)
        if self.target_cpu != self.current_cpu:
            current = 'x86' if forcex86 else self.current_cpu
            path = path.replace('\\', '\\%s_' % current)
        return path


class RegistryInfo:
    """
    Find Microsoft Visual C++ compiler related paths using registry or
    default paths.

    Parameters
    ----------
    platform_info: platform_info
        "platform_info" instance.
    version: float
        Required Microsoft Visual C++ version.
    """
    def __init__(self, platform_info, version):
        self.pi = platform_info
        self.version = version

    @property
    def microsoft(self):
        """
        Microsoft registry path.
        """
        return os.path.join(
            'Software',
            '' if self.pi.current_is_x86() else 'Wow6432Node',
            'Microsoft',
        )

    @property
    def sxs(self):
        """
        Visual Studio SxS registry path.
        """
        return os.path.join(self.microsoft, r'VisualStudio\SxS')

    @property
    def vc(self):
        """
        Visual C++ registry path.
        """
        return os.path.join(self.sxs, 'VC7')

    @property
    def vs(self):
        """
        Visual Studio registry path.
        """
        return os.path.join(self.sxs, 'VS7')

    @property
    def vc_for_python(self):
        """
        Visual C++ for Python.
        """
        path = r'DevDiv\VCForPython\%0.1f' % self.version
        return os.path.join(self.microsoft, path)

    @property
    def windows_sdk(self):
        """
        Windows/Platform SDK registry path.
        """
        return os.path.join(self.microsoft, r'Microsoft SDKs\Windows')

    def find_visual_studio(self):
        """
        Find Microsoft Visual Studio directory.
        """
        # Default path
        name = 'Microsoft Visual Studio %0.1f' % self.version
        default = os.path.join(self.pi.program_files_x86, name)

        # Try to get path from registry, if fail use default path
        return self._lookup(self.vs, '%0.1f' % self.version) or default

    def find_visual_c(self):
        """
        Find Microsoft Visual C++ directory.
        """
        # Default path
        default = r'Microsoft Visual Studio %0.1f\VC' % self.version
        guess_vc = os.path.join(self.pi.program_files_x86, default)

        # Try to get "VC++ for Python" path from registry as default path
        python_vc = self._lookup(self.vc_for_python, 'installdir')
        default_vc = os.path.join(python_vc, 'VC') if python_vc else guess_vc

        # Try to get path from registry, if fail use default path
        result = self._lookup(self.vc, '%0.1f' % self.version) or default_vc

        if not os.path.isdir(result):
            msg = 'vcvarsall.bat and Visual C++ directory not found'
            raise distutils.errors.DistutilsPlatformError(msg)

        return result

    def find_windows_sdk(self):
        """
        Find Microsoft Windows SDK directory.
        """
        WindowsSdkDir = ''
        if self.version == 9.0:
            WindowsSdkVer = ('7.0', '6.1', '6.0a')
        elif self.version == 10.0:
            WindowsSdkVer = ('7.1', '7.0a')
        else:
            WindowsSdkVer = ()
        for ver in WindowsSdkVer:
            # Try to get it from registry
            loc = os.path.join(self.windows_sdk, 'v%s' % ver)
            WindowsSdkDir = self._lookup(loc, 'installationfolder')
            if WindowsSdkDir:
                break
        if not WindowsSdkDir or not os.path.isdir(WindowsSdkDir):
            # Try to get "VC++ for Python" version from registry
            install_base = self._lookup(self.vc_for_python, 'installdir')
            if install_base:
                WindowsSdkDir = os.path.join(install_base, 'WinSDK')
        if not WindowsSdkDir or not os.path.isdir(WindowsSdkDir):
            # If fail, use default path
            for ver in WindowsSdkVer:
                path = r'Microsoft SDKs\Windows\v%s' % ver
                d = os.path.join(self.pi.program_files, path)
                if os.path.isdir(d):
                    WindowsSdkDir = d
        if not WindowsSdkDir:
            # If fail, use Platform SDK
            WindowsSdkDir = os.path.join(self.find_visual_c(), 'PlatformSDK')
        return WindowsSdkDir

    def find_dot_net_versions(self):
        """
        Find Microsoft .NET Framework Versions.
        """
        if self.version == 10.0:
            v4 = self._lookup(self.vc, 'frameworkver32') or ''
            if v4.lower()[:2] != 'v4':
                v4 = None
            # default to last v4 version
            v4 = v4 or 'v4.0.30319'
            FrameworkVer = (v4, 'v3.5')
        elif self.version == 9.0:
            FrameworkVer = ('v3.5', 'v2.0.50727')
        elif self.version == 8.0:
            FrameworkVer = ('v3.0', 'v2.0.50727')
        return FrameworkVer

    def find_dot_net_32(self):
        """
        Find Microsoft .NET Framework 32bit directory.
        """
        # Default path
        guess_fw = os.path.join(self.pi.win_dir, r'Microsoft.NET\Framework')

        # Try to get path from registry, if fail use default path
        return self._lookup(self.vc, 'frameworkdir32') or guess_fw

    def find_dot_net_64(self):
        """
        Find Microsoft .NET Framework 64bit directory.
        """
        # Default path
        guess_fw = os.path.join(self.pi.win_dir, r'Microsoft.NET\Framework64')

        # Try to get path from registry, if fail use default path
        return self._lookup(self.vc, 'frameworkdir64') or guess_fw

    def _lookup(self, base, key):
        try:
            return msvc9compiler.Reg.get_value(base, key)
        except KeyError:
            pass


def _compute_env(version, arch):
    """
    Return environment variables for specified Microsoft Visual C++ version
    and platform.

    Microsoft Visual C++ known compatibles versions
    -----------------------------------------------
    9.0, 10.0, 14.0
    """
    pi = PlatformInfo(arch)
    reg = RegistryInfo(pi, version)

    # Set Microsoft Visual Studio Tools
    paths = [r'Common7\IDE', r'Common7\Tools']
    if version >= 14.0:
        paths.append(r'Common7\IDE\CommonExtensions\Microsoft\TestWindow')
        paths.append(r'Team Tools\Performance Tools')
        paths.append(r'Team Tools\Performance Tools' + pi.ccpu_dir(True, True))
    VSTools = [os.path.join(reg.find_visual_studio(), path) for path in paths]

    # Set Microsoft Visual C++ & Microsoft Foundation Class Includes
    VCIncludes = [os.path.join(reg.find_visual_c(), 'Include'),
                  os.path.join(reg.find_visual_c(), 'ATLMFC\Include')]

    # Set Microsoft Visual C++ & Microsoft Foundation Class Libraries
    paths = ['Lib' + pi.tcpu_dir(True), r'ATLMFC\Lib' + pi.tcpu_dir(True)]
    if version >= 14.0:
        paths.append(r'Lib\store' + pi.tcpu_dir(True))
    VCLibraries = [os.path.join(reg.find_visual_c(), path) for path in paths]

    # Set Microsoft Visual C++ store references Libraries
    if version >= 14.0:
        path = r'Lib\store\references'
        VCStoreRefs = [os.path.join(reg.find_visual_c(), path)]
    else:
        VCStoreRefs = []

    # Set Microsoft Visual C++ Tools
    path = 'Bin' + pi.tools_extra(False if version >= 14.0 else True)
    VCTools = [
        os.path.join(reg.find_visual_c(), 'VCPackages'),
        os.path.join(reg.find_visual_c(), path),
    ]
    if pi.tools_extra() and version >= 14.0:
        path = 'Bin' + pi.ccpu_dir(True)
        VCTools.append(os.path.join(reg.find_visual_c(), path))
    else:
        VCTools.append(os.path.join(reg.find_visual_c(), 'Bin'))

    # Set Microsoft Windows SDK Libraries
    path = 'Lib' + pi.tcpu_dir(True, True)
    OSLibraries = [os.path.join(reg.find_windows_sdk(), path)]

    # Set Microsoft Windows SDK Include
    OSIncludes = [
        os.path.join(reg.find_windows_sdk(), 'Include'),
        os.path.join(reg.find_windows_sdk(), r'Include\gl'),
    ]

    # Set Microsoft Windows SDK Tools
    SdkTools = [os.path.join(reg.find_windows_sdk(), 'Bin')]
    if not pi.target_is_x86():
        path = 'Bin' + pi.tcpu_dir(True, True)
        SdkTools.append(os.path.join(reg.find_windows_sdk(), path))
    if version == 10.0:
        path = r'Bin\NETFX 4.0 Tools' + pi.tcpu_dir(True, True)
        SdkTools.append(os.path.join(reg.find_windows_sdk(), path))

    # Set Microsoft Windows SDK Setup
    SdkSetup = [os.path.join(reg.find_windows_sdk(), 'Setup')]

    # Set Microsoft .NET Framework Tools
    roots = [reg.find_dot_net_32()]
    include_64_framework = not pi.target_is_x86() and not pi.current_is_x86()
    roots += [reg.find_dot_net_64()] if include_64_framework else []

    FxTools = [
        os.path.join(root, ver)
        for root, ver in itertools.product(roots, reg.find_dot_net_versions())
    ]

    # Set Microsoft Visual Studio Team System Database
    VsTDb = [os.path.join(reg.find_visual_studio(), r'VSTSDB\Deploy')]

    # Set Microsoft Build Engine
    path = r'\MSBuild\%0.1f\bin%s' % (version, pi.ccpu_dir(True))
    MSBuild = [
        os.path.join(pi.program_files_x86, path),
        os.path.join(pi.program_files, path)
    ]

    # Set Microsoft HTML Help Workshop
    path = 'HTML Help Workshop'
    HTMLWork = [
        os.path.join(pi.program_files_x86, path),
        os.path.join(pi.program_files, path)
    ]

    # Return environment
    return dict(
        include=_build_paths('include', [VCIncludes, OSIncludes]),
        lib=_build_paths('lib', [VCLibraries, OSLibraries, FxTools]),
        libpath=_build_paths('libpath', [VCLibraries, FxTools, VCStoreRefs]),
        path=_build_paths('path', [VCTools, VSTools, VsTDb, SdkTools, SdkSetup,
                                   FxTools, MSBuild, HTMLWork]),
    )


def _build_paths(name, spec_path_lists):
    """
    Given an environment variable name and specified paths,
    return a pathsep-separated string of paths containing
    unique, extant, directories from those paths and from
    the environment variable. Raise an error if no paths
    are resolved.
    """
    # flatten spec_path_lists
    spec_paths = itertools.chain.from_iterable(spec_path_lists)
    env_paths = os.environ.get(name, '').split(os.pathsep)
    paths = itertools.chain(spec_paths, env_paths)
    extant_paths = list(filter(os.path.isdir, paths))
    if not extant_paths:
        msg = "%s environment variable is empty" % name.upper()
        raise distutils.errors.DistutilsPlatformError(msg)
    unique_paths = _unique_everseen(extant_paths)
    return os.pathsep.join(unique_paths)


# from Python docs
def _unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    filterfalse = six.moves.filterfalse
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element
