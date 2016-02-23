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
        import os
        vcvarsall = os.path.join(productdir, "vcvarsall.bat")
        if os.path.isfile(vcvarsall):
            return vcvarsall

    return unpatched['find_vcvarsall'](version)

def query_vcvarsall(version, *args, **kwargs):
    message = ''

    # Try to get environement from vcvarsall.bat (Classical way)
    try:
        return unpatched['query_vcvarsall'](version, *args, **kwargs)
    except distutils.errors.DistutilsPlatformError as exc:
        # Error if Vcvarsall.bat is missing
        message = exc.args[0]
    except ValueError as exc:
        # Error if environment not set after executing vcvarsall.bat
        message = exc.args[0]

    # If vcvarsall.bat fail, try to set environment directly
    try:
        if not args:
            arch = 'x86'
        else:
            arch = args[0]
        return setvcenv(version, kwargs.get('arch', arch))
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
    raise distutils.errors.DistutilsPlatformError(message)

def setvcenv(version, arch):
    """
    Return environment variables for specified Microsoft Visual C++ version
    and platform.
    """
    from os.path import join, isdir
    from os import environ
    from distutils.errors import DistutilsPlatformError

    # Find current and target architecture
    CurrentCpu = environ['processor_architecture'].lower()
    TargetCpu = arch[arch.find('_') + 1:]
    Tar_not_x86 = TargetCpu != 'x86'
    Cur_not_x86 = CurrentCpu != 'x86'

    # Find "Windows" and "Program Files" system directories
    WinDir = environ['WinDir']
    ProgramFiles = environ['ProgramFiles']
    ProgramFilesX86 = environ.get('ProgramFiles(x86)', ProgramFiles)

    # Set registry base paths
    reg_value = distutils.msvc9compiler.Reg.get_value
    node = r'\Wow6432Node' if Cur_not_x86 else ''
    VsReg = r'Software%s\Microsoft\VisualStudio\SxS\VS7' % node
    VcReg = r'Software%s\Microsoft\VisualStudio\SxS\VC7' % node
    VcForPythonReg = r'Software%s\Microsoft\DevDiv\VCForPython\%0.1f' %\
        (node, version)
    WindowsSdkReg = r'Software%s\Microsoft\Microsoft SDKs\Windows' % node

    # Set Platform subdirectories
    if TargetCpu == 'amd64':
        plt_subd_lib = r'\amd64'
        plt_subd_sdk = r'\x64'
        if CurrentCpu == 'amd64':
            plt_subd_tools = r'\amd64'
        else:
            plt_subd_tools = r'\x86_amd64'
    elif TargetCpu == 'ia64':
        plt_subd_lib = r'\ia64'
        plt_subd_sdk = r'\ia64'
        if CurrentCpu == 'ia64':
            plt_subd_tools = r'\ia64'
        else:
            plt_subd_tools = r'\x86_ia64'
    else:
        plt_subd_lib = ''
        plt_subd_sdk = ''
        plt_subd_tools = ''

    # Find Microsoft Visual Studio directory
    try:
        # Try to get it from registry
        VsInstallDir = reg_value(VsReg, '%0.1f' % version)
    except KeyError:
        # If fail, use default path
        VsInstallDir = join(ProgramFilesX86,
                            'Microsoft Visual Studio %0.1f' % version)

    # Find Microsoft Visual C++ directory
    try:
        # Try to get it from registry
        VcInstallDir = reg_value(VcReg, '%0.1f' % version)
    except KeyError:
        try:
            # Try to get "VC++ for Python" version from registry
            VcInstallDir = join(reg_value(VcForPythonReg, 'installdir'), 'VC')
        except KeyError:
            # If fail, use default path
            VcInstallDir = join(ProgramFilesX86,
                                r'Microsoft Visual Studio %0.1f\VC' % version)
    if not isdir(VcInstallDir):
        raise DistutilsPlatformError('vcvarsall.bat and Visual C++ '
                                     'directory not found')

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
        try:
            WindowsSdkDir = reg_value(join(WindowsSdkReg, 'v%s' % ver),
                                      'installationfolder')
            break
        except KeyError:
            pass
    if not WindowsSdkDir or not isdir(WindowsSdkDir):
        # Try to get "VC++ for Python" version from registry
        try:
            WindowsSdkDir = join(reg_value(VcForPythonReg, 'installdir'),
                                 'WinSDK')
        except:
            pass
    if not WindowsSdkDir or not isdir(WindowsSdkDir):
        # If fail, use default path
        for ver in WindowsSdkVer:
            d = join(ProgramFiles, r'Microsoft SDKs\Windows\v%s' % ver)
            if isdir(d):
                WindowsSdkDir = d
    if not WindowsSdkDir:
        # If fail, use Platform SDK
        WindowsSdkDir = join(VcInstallDir, 'PlatformSDK')

    # Find Microsoft .NET Framework 32bit directory
    try:
        # Try to get it from registry
        FrameworkDir32 = reg_value(VcReg, 'frameworkdir32')
    except KeyError:
        # If fail, use default path
        FrameworkDir32 = join(WinDir, r'Microsoft.NET\Framework')

    # Find Microsoft .NET Framework 64bit directory
    try:
        # Try to get it from registry
        FrameworkDir64 = reg_value(VcReg, 'frameworkdir64')
    except KeyError:
        # If fail, use default path
        FrameworkDir64 = join(WinDir, r'Microsoft.NET\Framework64')

    # Find Microsoft .NET Framework Versions
    if version == 10.0:
        try:
            # Try to get v4 from registry
            v4 = reg_value(VcReg, 'frameworkver32')
            if v4.lower()[:2] != 'v4':
                raise KeyError('Not the V4')
        except KeyError:
            # If fail, use last v4 version
            v4 = 'v4.0.30319'
        FrameworkVer = (v4, 'v3.5')
    elif version == 9.0:
        FrameworkVer = ('v3.5', 'v2.0.50727')
    elif version == 8.0:
        FrameworkVer = ('v3.0', 'v2.0.50727')

    # Set Microsoft Visual Studio Tools
    VSTools = [join(VsInstallDir, r'Common7\IDE'),
               join(VsInstallDir, r'Common7\Tools')]

    # Set Microsoft Visual C++ Includes
    VCIncludes = [join(VcInstallDir, 'Include')]

    # Set Microsoft Visual C++ & Microsoft Foundation Class Libraries
    VCLibraries = [join(VcInstallDir, 'Lib' + plt_subd_lib),
                   join(VcInstallDir, r'ATLMFC\LIB' + plt_subd_lib)]

    # Set Microsoft Visual C++ Tools
    VCTools = [join(VcInstallDir, 'VCPackages'),
               join(VcInstallDir, 'Bin' + plt_subd_tools)]
    if plt_subd_tools:
        VCTools.append(join(VcInstallDir, 'Bin'))

    # Set Microsoft Windows SDK Include
    OSLibraries = [join(WindowsSdkDir, 'Lib' + plt_subd_sdk)]

    # Set Microsoft Windows SDK Libraries
    OSIncludes = [join(WindowsSdkDir, 'Include'),
                  join(WindowsSdkDir, r'Include\gl')]

    # Set Microsoft Windows SDK Tools
    SdkTools = [join(WindowsSdkDir, 'Bin')]
    if Tar_not_x86:
        SdkTools.append(join(WindowsSdkDir, 'Bin' + plt_subd_sdk))
    if version == 10.0:
        SdkTools.append(join(WindowsSdkDir,
                             r'Bin\NETFX 4.0 Tools' + plt_subd_sdk))

    # Set Microsoft Windows SDK Setup
    SdkSetup = [join(WindowsSdkDir, 'Setup')]

    # Set Microsoft .NET Framework Tools
    FxTools = [join(FrameworkDir32, ver) for ver in FrameworkVer]
    if Tar_not_x86 and Cur_not_x86:
        for ver in FrameworkVer:
            FxTools.append(join(FrameworkDir64, ver))

    # Set Microsoft Visual Studio Team System Database
    VsTDb = [join(VsInstallDir, r'VSTSDB\Deploy')]

    # Return Environment Variables
    env = {}
    env['include'] = [VCIncludes, OSIncludes]
    env['lib'] = [VCLibraries, OSLibraries, FxTools]
    env['libpath'] = [VCLibraries, FxTools]
    env['path'] = [VCTools, VSTools, VsTDb, SdkTools, SdkSetup, FxTools]

    def checkpath(path, varlist):
        # Function that add valid paths in list in not already present
        if isdir(path) and path not in varlist:
            varlist.append(path)

    for key in env.keys():
        var = []
        # Add valid paths
        for val in env[key]:
            for subval in val:
                checkpath(subval, var)

        # Add values from actual environment
        try:
            for val in environ[key].split(';'):
                checkpath(val, var)
        except KeyError:
            pass

        # Format paths to Environment Variable string
        if var:
            env[key] = ';'.join(var)
        else:
            raise DistutilsPlatformError("%s environment variable is empty" %
                                         key.upper())
    return env
