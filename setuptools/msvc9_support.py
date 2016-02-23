import os
import distutils.errors

try:
    import distutils.msvc9compiler
except ImportError:
    pass

unpatched = dict()

def patch_for_specialized_compiler():
    """
    Patch functions in distutils.msvc9compiler to use the standalone compiler
    build for Python (Windows only). Fall back to original behavior when the
    standalone compiler is not available.
    """
    if 'distutils' not in globals():
        # The module isn't available to be patched
        return

    if unpatched:
        # Already patched
        return

    unpatched.update(vars(distutils.msvc9compiler))

    distutils.msvc9compiler.find_vcvarsall = find_vcvarsall
    distutils.msvc9compiler.query_vcvarsall = query_vcvarsall

def find_vcvarsall(version):
    Reg = distutils.msvc9compiler.Reg
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

    return unpatched['find_vcvarsall'](version)

def query_vcvarsall(version, arch='x86', *args, **kwargs):
    message = ''

    # Try to get environement from vcvarsall.bat (Classical way)
    try:
        return unpatched['query_vcvarsall'](version, arch, *args, **kwargs)
    except distutils.errors.DistutilsPlatformError as exc:
        # Error if Vcvarsall.bat is missing
        message = exc.args[0]
    except ValueError as exc:
        # Error if environment not set after executing vcvarsall.bat
        message = exc.args[0]

    # If vcvarsall.bat fail, try to set environment directly
    try:
        return _query_vcvarsall(version, arch)
    except distutils.errors.DistutilsPlatformError as exc:
        # Error if MSVC++ directory not found or environment not set
        message = exc.args[0]

    # Raise error
    if message and "vcvarsall.bat" in message:
        # Special error message if MSVC++ not installed
        message = 'Microsoft Visual C++ %0.1f is required (%s).' %\
            (version, message)
        if int(version) == 9:
            # For VC++ 9.0 Redirect user to Vc++ for Python 2.7 :
            # This redirection link is maintained by Microsoft.
            # Contact vspython@microsoft.com if it needs updating.
            message += r' Get it from http://aka.ms/vcpython27'
        elif int(version) == 10:
            # For VC++ 10.0 Redirect user to Windows SDK 7.1
            message += ' Get it with "Microsoft Windows SDK for Windows 7": '
            message += r'www.microsoft.com/download/details.aspx?id=8279'

    raise distutils.errors.DistutilsPlatformError(message)


class PlatformInfo:
    current_cpu = os.environ['processor_architecture'].lower()
    win_dir = os.environ['WinDir']
    program_files = os.environ['ProgramFiles']
    program_files_x86 = os.environ.get('ProgramFiles(x86)', program_files)

    def __init__(self, arch):
        self.arch = arch

    @property
    def target_cpu(self):
        return self.arch[self.arch.find('_') + 1:]

    def target_is_x86(self):
        return self.target_cpu == 'x86'

    def current_is_x86(self):
        return self.current_cpu != 'x86'

    @property
    def lib_extra(self):
        return (
            r'\amd64' if self.target_cpu == 'amd64' else
            r'\ia64' if self.target_cpu == 'ia64' else
            ''
        )

    @property
    def sdk_extra(self):
        return (
            r'\x64' if self.target_cpu == 'amd64' else
            r'\ia64' if self.target_cpu == 'ia64' else
            ''
        )

    @property
    def tools_extra(self):
        path = self.lib_extra
        if self.target_cpu != self.current_cpu:
            path = path.replace('\\', '\\x86_')
        return path


class RegistryInfo:
    def __init__(self, platform_info, version):
        self.platform_info = platform_info
        self.version = version

    @property
    def microsoft(self):
        return os.path.join(
            'Software',
            '' if self.platform_info.current_is_x86() else 'Wow6432Node',
            'Microsoft',
        )

    @property
    def sxs(self):
        return os.path.join(self.microsoft, r'VisualStudio\SxS')

    @property
    def vc(self):
        return os.path.join(self.sxs, 'VC7')

    @property
    def vs(self):
        return os.path.join(self.sxs, 'VS7')

    @property
    def vc_for_python(self):
        path = r'DevDiv\VCForPython\%0.1f' % self.version
        return os.path.join(self.microsoft, path)

    @property
    def windows_sdk(self):
        return os.path.join(self.microsoft, r'Microsoft SDKs\Windows')

    def find_visual_studio(self):
        """
        Find Microsoft Visual Studio directory
        """
        name = 'Microsoft Visual Studio %0.1f' % self.version
        default = os.path.join(self.platform_info.program_files_x86, name)
        return self.lookup(self.vs, '%0.1f' % self.version) or default

    def lookup(self, base, key):
        try:
            return distutils.msvc9compiler.Reg.get_value(base, key)
        except KeyError:
            pass


def _query_vcvarsall(version, arch):
    """
    Return environment variables for specified Microsoft Visual C++ version
    and platform.
    """
    pi = PlatformInfo(arch)
    reg = RegistryInfo(pi, version)
    reg_value = reg.lookup

    # Find Microsoft Visual C++ directory

    # If fail, use default path
    default = r'Microsoft Visual Studio %0.1f\VC' % version
    guess_vc = os.path.join(pi.program_files_x86, default)

    # Try to get "VC++ for Python" version from registry
    install_base = reg_value(reg.vc_for_python, 'installdir')
    default_vc = os.path.join(install_base, 'VC') if install_base else guess_vc

    VcInstallDir = reg_value(reg.vc, '%0.1f' % version) or default_vc

    if not os.path.isdir(VcInstallDir):
        msg = 'vcvarsall.bat and Visual C++ directory not found'
        raise distutils.errors.DistutilsPlatformError(msg)

    # Find Microsoft Windows SDK directory
    WindowsSdkDir = ''
    if version == 9.0:
        WindowsSdkVer = ('7.0', '6.1', '6.0a')
    elif version == 10.0:
        WindowsSdkVer = ('7.1', '7.0a')
    else:
        WindowsSdkVer = ()
    for ver in WindowsSdkVer:
        # Try to get it from registry
        loc = os.path.join(reg.windows_sdk, 'v%s' % ver)
        WindowsSdkDir = reg_value(loc, 'installationfolder')
        if WindowsSdkDir:
            break
    if not WindowsSdkDir or not os.path.isdir(WindowsSdkDir):
        # Try to get "VC++ for Python" version from registry
        install_base = reg_value(reg.vc_for_python, 'installdir')
        if install_base:
            WindowsSdkDir = os.path.join(install_base, 'WinSDK')
    if not WindowsSdkDir or not os.path.isdir(WindowsSdkDir):
        # If fail, use default path
        for ver in WindowsSdkVer:
            path = r'Microsoft SDKs\Windows\v%s' % ver
            d = os.path.join(pi.program_files, path)
            if os.path.isdir(d):
                WindowsSdkDir = d
    if not WindowsSdkDir:
        # If fail, use Platform SDK
        WindowsSdkDir = os.path.join(VcInstallDir, 'PlatformSDK')

    # Find Microsoft .NET Framework 32bit directory
    guess_fw = os.path.join(pi.win_dir, r'Microsoft.NET\Framework')
    FrameworkDir32 = reg_value(reg.vc, 'frameworkdir32') or guess_fw

    # Find Microsoft .NET Framework 64bit directory
    guess_fw64 = os.path.join(pi.win_dir, r'Microsoft.NET\Framework64')
    FrameworkDir64 = reg_value(reg.vc, 'frameworkdir64') or guess_fw64

    # Find Microsoft .NET Framework Versions
    if version == 10.0:
        v4 = reg_value(reg.vc, 'frameworkver32') or ''
        if v4.lower()[:2] != 'v4':
            v4 = None
        # default to last v4 version
        v4 = v4 or 'v4.0.30319'
        FrameworkVer = (v4, 'v3.5')
    elif version == 9.0:
        FrameworkVer = ('v3.5', 'v2.0.50727')
    elif version == 8.0:
        FrameworkVer = ('v3.0', 'v2.0.50727')

    # Set Microsoft Visual Studio Tools
    VSTools = [
        os.path.join(reg.find_visual_studio(), r'Common7\IDE'),
        os.path.join(reg.find_visual_studio(), r'Common7\Tools'),
    ]

    # Set Microsoft Visual C++ Includes
    VCIncludes = [os.path.join(VcInstallDir, 'Include')]

    # Set Microsoft Visual C++ & Microsoft Foundation Class Libraries
    VCLibraries = [
        os.path.join(VcInstallDir, 'Lib' + pi.lib_extra),
        os.path.join(VcInstallDir, r'ATLMFC\LIB' + pi.lib_extra),
    ]

    # Set Microsoft Visual C++ Tools
    VCTools = [
        os.path.join(VcInstallDir, 'VCPackages'),
        os.path.join(VcInstallDir, 'Bin' + pi.tools_extra),
    ]
    if pi.tools_extra:
        VCTools.append(os.path.join(VcInstallDir, 'Bin'))

    # Set Microsoft Windows SDK Include
    OSLibraries = [os.path.join(WindowsSdkDir, 'Lib' + pi.sdk_extra)]

    # Set Microsoft Windows SDK Libraries
    OSIncludes = [
        os.path.join(WindowsSdkDir, 'Include'),
        os.path.join(WindowsSdkDir, r'Include\gl'),
    ]

    # Set Microsoft Windows SDK Tools
    SdkTools = [os.path.join(WindowsSdkDir, 'Bin')]
    if not pi.target_is_x86():
        SdkTools.append(os.path.join(WindowsSdkDir, 'Bin' + pi.sdk_extra))
    if version == 10.0:
        path = r'Bin\NETFX 4.0 Tools' + pi.sdk_extra
        SdkTools.append(os.path.join(WindowsSdkDir, path))

    # Set Microsoft Windows SDK Setup
    SdkSetup = [os.path.join(WindowsSdkDir, 'Setup')]

    # Set Microsoft .NET Framework Tools
    FxTools = [os.path.join(FrameworkDir32, ver) for ver in FrameworkVer]
    if not pi.target_is_x86() and not pi.current_is_x86():
        for ver in FrameworkVer:
            FxTools.append(os.path.join(FrameworkDir64, ver))

    # Set Microsoft Visual Studio Team System Database
    VsTDb = [os.path.join(reg.find_visual_studio(), r'VSTSDB\Deploy')]

    # Return Environment Variables
    env = {}
    env['include'] = [VCIncludes, OSIncludes]
    env['lib'] = [VCLibraries, OSLibraries, FxTools]
    env['libpath'] = [VCLibraries, FxTools]
    env['path'] = [VCTools, VSTools, VsTDb, SdkTools, SdkSetup, FxTools]

    def checkpath(path, varlist):
        # Function that add valid paths in list in not already present
        if os.path.isdir(path) and path not in varlist:
            varlist.append(path)

    for key in env.keys():
        var = []
        # Add valid paths
        for val in env[key]:
            for subval in val:
                checkpath(subval, var)

        # Add values from actual environment
        try:
            for val in os.environ[key].split(';'):
                checkpath(val, var)
        except KeyError:
            pass

        # Format paths to Environment Variable string
        if var:
            env[key] = ';'.os.path.join(var)
        else:
            msg = "%s environment variable is empty" % key.upper()
            raise distutils.errors.DistutilsPlatformError(msg)
    return env
