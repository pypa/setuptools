/*  Setuptools Script Launcher for Windows

    This is a stub executable for Windows that functions somewhat like
    Effbot's "exemaker", in that it runs a script with the same name but
    a .py extension, using information from a #! line.  It differs in that
    it spawns the actual Python executable, rather than attempting to
    hook into the Python DLL.  This means that the script will run with
    sys.executable set to the Python executable, where exemaker ends up with
    sys.executable pointing to itself.  (Which means it won't work if you try
    to run another Python process using sys.executable.)

    To build/rebuild with mingw32, do this in the setuptools project directory:

       gcc -DGUI=0           -mno-cygwin -O -s -o setuptools/cli.exe launcher.c
       gcc -DGUI=1 -mwindows -mno-cygwin -O -s -o setuptools/gui.exe launcher.c

    To build for Windows RT, install both Visual Studio Express for Windows 8
    and for Windows Desktop (both freeware), create "win32" application using
    "Windows Desktop" version, create new "ARM" target via
    "Configuration Manager" menu and modify ".vcxproj" file by adding
    "<WindowsSDKDesktopARMSupport>true</WindowsSDKDesktopARMSupport>" tag
    as child of "PropertyGroup" tags that has "Debug|ARM" and "Release|ARM"
    properties.

    It links to msvcrt.dll, but this shouldn't be a problem since it doesn't
    actually run Python in the same process.  Note that using 'exec' instead
    of 'spawn' doesn't work, because on Windows this leads to the Python
    executable running in the *background*, attached to the same console
    window, meaning you get a command prompt back *before* Python even finishes
    starting.  So, we have to use spawnv() and wait for Python to exit before
    continuing.  :(
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include <wchar.h>
#include <io.h>
#include <fcntl.h>

int child_pid=0;

int fail(wchar_t *format, wchar_t *data) {
    /* Print error message to stderr and return 2 */
    /* set stderr mode to Unicode UTF-16 to print wchar_t* to the console */
    _setmode(_fileno(stderr), _O_U16TEXT);
    fwprintf(stderr, format, data);
    return 2;
}

wchar_t *quoted(wchar_t *data) {
    int nb;
    size_t i, ln = wcslen(data);

    /* We allocate twice as much space as needed to deal with worse-case
       of having to escape everything. */
    wchar_t *result = calloc(ln*2+3, sizeof(wchar_t));
    wchar_t *presult = result;

    *presult++ = L'"';
    for (nb=0, i=0; i < ln; i++)
      {
        if (data[i] == L'\\')
          nb += 1;
        else if (data[i] == L'"')
          {
            for (; nb > 0; nb--)
              *presult++ = L'\\';
            *presult++ = L'\\';
          }
        else
          nb = 0;
        *presult++ = data[i];
      }

    for (; nb > 0; nb--)        /* Deal w trailing slashes */
      *presult++ = L'\\';

    *presult++ = L'"';
    *presult++ = 0;
    return result;
}










wchar_t *loadable_exe(wchar_t *exename) {
    /* HINSTANCE hPython;  DLL handle for python executable */
    wchar_t *result;

    /* hPython = LoadLibraryEx(exename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!hPython) return NULL; */

    /* Return the absolute filename for spawnv */
    result = calloc(MAX_PATH, sizeof(wchar_t));
    wcsncpy(result, exename, MAX_PATH);
    /*if (result) GetModuleFileNameA(hPython, result, MAX_PATH);

    FreeLibrary(hPython); */
    return result;
}


wchar_t *find_exe(wchar_t *exename, wchar_t *script) {
    wchar_t drive[_MAX_DRIVE], dir[_MAX_DIR], fname[_MAX_FNAME], ext[_MAX_EXT];
    wchar_t path[_MAX_PATH], c, *result;

    /* convert slashes to backslashes for uniform search below */
    result = exename;
    while (c = *result++) if (c==L'/') result[-1] = L'\\';

    _wsplitpath(exename, drive, dir, fname, ext);
    if (drive[0] || dir[0]==L'\\') {
        return loadable_exe(exename);   /* absolute path, use directly */
    }
    /* Use the script's parent directory, which should be the Python home
       (This should only be used for bdist_wininst-installed scripts, because
        easy_install-ed scripts use the absolute path to python[w].exe
    */
    _wsplitpath(script, drive, dir, fname, ext);
    result = dir + wcslen(dir) -1;
    if (*result == L'\\') result--;
    while (*result != L'\\' && result>=dir) *result-- = 0;
    _wmakepath(path, drive, dir, exename, NULL);
    return loadable_exe(path);
}


wchar_t **parse_argv(wchar_t *cmdline, int *argc)
{
    /* Parse a command line in-place using MS C rules */

    wchar_t **result = calloc(wcslen(cmdline), sizeof(wchar_t *));
    wchar_t *output = cmdline;
    wchar_t c;
    int nb = 0;
    int iq = 0;
    *argc = 0;

    result[0] = output;
    while (iswspace(*cmdline)) cmdline++;   /* skip leading spaces */

    do {
        c = *cmdline++;
        if (!c || (iswspace(c) && !iq)) {
            while (nb) {*output++ = L'\\'; nb--; }
            *output++ = 0;
            result[++*argc] = output;
            if (!c) return result;
            while (iswspace(*cmdline)) cmdline++;  /* skip leading spaces */
            if (!*cmdline) return result;  /* avoid empty arg if trailing ws */
            continue;
        }
        if (c == L'\\')
            ++nb;   /* count \'s */
        else {
            if (c == L'"') {
                if (!(nb & 1)) { iq = !iq; c = 0; }  /* skip " unless odd # of \ */
                nb = nb >> 1;   /* cut \'s in half */
            }
            while (nb) {*output++ = L'\\'; nb--; }
            if (c) *output++ = c;
        }
    } while (1);
}

void pass_control_to_child(DWORD control_type) {
    /*
     * distribute-issue207
     * passes the control event to child process (Python)
     */
    if (!child_pid) {
        return;
    }
    GenerateConsoleCtrlEvent(child_pid,0);
}

BOOL control_handler(DWORD control_type) {
    /* 
     * distribute-issue207
     * control event handler callback function
     */
    switch (control_type) {
        case CTRL_C_EVENT:
            pass_control_to_child(0);
            break;
    }
    return TRUE;
}

int create_and_wait_for_subprocess(wchar_t * command) {
    /*
     * distribute-issue207
     * launches child process (Python)
     */
    DWORD return_value = 0;
    LPWSTR commandline = command;
    STARTUPINFOW s_info;
    PROCESS_INFORMATION p_info;
    ZeroMemory(&p_info, sizeof(p_info));
    ZeroMemory(&s_info, sizeof(s_info));
    s_info.cb = sizeof(STARTUPINFO);
    // set-up control handler callback funciotn
    SetConsoleCtrlHandler((PHANDLER_ROUTINE) control_handler, TRUE);
    if (!CreateProcessW(NULL, commandline, NULL, NULL, TRUE, 0, NULL, NULL, &s_info, &p_info)) {
        fprintf(stderr, "failed to create process.\n");
        return 0;
    }   
    child_pid = p_info.dwProcessId;
    // wait for Python to exit
    WaitForSingleObject(p_info.hProcess, INFINITE);
    if (!GetExitCodeProcess(p_info.hProcess, &return_value)) {
        fprintf(stderr, "failed to get exit code from process.\n");
        return 0;
    }
    return return_value;
}

wchar_t* join_executable_and_args(wchar_t *executable, wchar_t **args, int argc)
{
    /*
     * distribute-issue207
     * CreateProcess needs a long string of the executable and command-line arguments,
     * so we need to convert it from the args that was built
     */
    int counter;
    size_t maxlen, len;
    wchar_t* cmdline;
    
    maxlen=wcslen(executable)+2;
    for (counter=1; counter<argc; counter++) {
        maxlen+=wcslen(args[counter])+1;
    }

    cmdline = (wchar_t*)calloc(maxlen, sizeof(wchar_t));
    len = swprintf(cmdline, maxlen, L"%s", executable);
    for (counter=1; counter<argc; counter++) {
        len += swprintf(cmdline+len, maxlen, L" %s", args[counter]);
    }
    return cmdline;
}

int run(int argc, wchar_t **argv, int is_gui) {

    wchar_t python[_MAX_PATH];   /* python executable's filename*/
    wchar_t script[_MAX_PATH];   /* the script's filename */

    FILE *scriptf;        /* file pointer for script file */

    wchar_t **newargs, **newargsp, **parsedargs; /* argument array for exec */
    wchar_t *ptr, *end;    /* working pointers for string manipulation */
    wchar_t *cmdline;
    int i, parsedargc;              /* loop counter */

    /* compute script name from our .exe name*/
    GetModuleFileNameW(NULL, script, sizeof(script));
    end = script + wcslen(script);
    while( end>script && *end != L'.')
        *end-- = L'\0';
    *end-- = L'\0';
    wcscat(script, (GUI ? L"-script.pyw" : L"-script.py"));

    /* figure out the target python executable */

    scriptf = _wfopen(script, L"rt,ccs=UTF-8");
    if (scriptf == NULL) {
        return fail(L"Cannot open %s\n", script);
    }
    end = python + fread(python, sizeof(wchar_t), sizeof(python)/sizeof(wchar_t), scriptf);
    fclose(scriptf);

    ptr = python-1;
    while(++ptr < end && *ptr && *ptr!='\n' && *ptr!='\r') {;}

    *ptr-- = '\0';

    if (wcsncmp(python, L"#!", 2)) {
        /* default to python.exe if no #! header */
        wcscpy(python, L"#!python.exe");
    }

    parsedargs = parse_argv(python+2, &parsedargc);

    /* Using spawnv() can fail strangely if you e.g. find the Cygwin
       Python, so we'll make sure Windows can find and load it */

    ptr = find_exe(parsedargs[0], script);
    if (!ptr) {
        return fail(L"Cannot find Python executable %s\n", parsedargs[0]);
    }

    /* printf("Python executable: %s\n", ptr); */

    /* Argument array needs to be
       parsedargc + argc, plus 1 for null sentinel */

    newargs = (wchar_t **)calloc(parsedargc + argc + 1, sizeof(wchar_t *));
    newargsp = newargs;

    *newargsp++ = quoted(ptr);
    for (i = 1; i<parsedargc; i++) *newargsp++ = quoted(parsedargs[i]);

    *newargsp++ = quoted(script);
    for (i = 1; i < argc; i++)     *newargsp++ = quoted(argv[i]);

    *newargsp++ = NULL;

    /* printf("args 0: %s\nargs 1: %s\n", newargs[0], newargs[1]); */

    if (is_gui) {
        /* Use exec, we don't need to wait for the GUI to finish */
        _wexecv(ptr, (const wchar_t * const *)(newargs));
        return fail(L"Could not exec %s", ptr);   /* shouldn't get here! */
    }

    /*
     * distribute-issue207: using CreateProcessW instead of spawnv
     */
    cmdline = join_executable_and_args(ptr, newargs, parsedargc + argc);

    return create_and_wait_for_subprocess(cmdline);
}

int WINAPI wWinMain(HINSTANCE hI, HINSTANCE hP, LPWSTR lpCmd, int nShow) {
    return run(__argc, __wargv, GUI);
}

int wmain(int argc, wchar_t ** argv) {
    return run(argc, argv, GUI);
}

