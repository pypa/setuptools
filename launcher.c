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
#include <unistd.h>
#include <fcntl.h>
#include "windows.h"

int fail(char *format, char *data) {
    /* Print error message to stderr and return 2 */
    fprintf(stderr, format, data);
    return 2;
}





char *quoted(char *data) {
    int i, ln = strlen(data), nb;

    /* We allocate twice as much space as needed to deal with worse-case
       of having to escape everything. */
    char *result = calloc(ln*2+3, sizeof(char));
    char *presult = result;

    *presult++ = '"';
    for (nb=0, i=0; i < ln; i++)
      {
        if (data[i] == '\\')
          nb += 1;
        else if (data[i] == '"')
          {
            for (; nb > 0; nb--)
              *presult++ = '\\';
            *presult++ = '\\';
          }
        else
          nb = 0;
        *presult++ = data[i];
      }

    for (; nb > 0; nb--)        /* Deal w trailing slashes */
      *presult++ = '\\';

    *presult++ = '"';
    *presult++ = 0;
    return result;
}










char *loadable_exe(char *exename) {
    /* HINSTANCE hPython;  DLL handle for python executable */
    char *result;

    /* hPython = LoadLibraryEx(exename, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!hPython) return NULL; */

    /* Return the absolute filename for spawnv */
    result = calloc(MAX_PATH, sizeof(char));
    strncpy(result, exename, MAX_PATH);
    /*if (result) GetModuleFileName(hPython, result, MAX_PATH);

    FreeLibrary(hPython); */
    return result;
}


char *find_exe(char *exename, char *script) {
    char drive[_MAX_DRIVE], dir[_MAX_DIR], fname[_MAX_FNAME], ext[_MAX_EXT];
    char path[_MAX_PATH], c, *result;

    /* convert slashes to backslashes for uniform search below */
    result = exename;
    while (c = *result++) if (c=='/') result[-1] = '\\';

    _splitpath(exename, drive, dir, fname, ext);
    if (drive[0] || dir[0]=='\\') {
        return loadable_exe(exename);   /* absolute path, use directly */
    }
    /* Use the script's parent directory, which should be the Python home
       (This should only be used for bdist_wininst-installed scripts, because
        easy_install-ed scripts use the absolute path to python[w].exe
    */
    _splitpath(script, drive, dir, fname, ext);
    result = dir + strlen(dir) -1;
    if (*result == '\\') result--;
    while (*result != '\\' && result>=dir) *result-- = 0;
    _makepath(path, drive, dir, exename, NULL);
    return loadable_exe(path);
}


char **parse_argv(char *cmdline, int *argc)
{
    /* Parse a command line in-place using MS C rules */

    char **result = calloc(strlen(cmdline), sizeof(char *));
    char *output = cmdline;
    char c;
    int nb = 0;
    int iq = 0;
    *argc = 0;

    result[0] = output;
    while (isspace(*cmdline)) cmdline++;   /* skip leading spaces */

    do {
        c = *cmdline++;
        if (!c || (isspace(c) && !iq)) {
            while (nb) {*output++ = '\\'; nb--; }
            *output++ = 0;
            result[++*argc] = output;
            if (!c) return result;
            while (isspace(*cmdline)) cmdline++;  /* skip leading spaces */
            if (!*cmdline) return result;  /* avoid empty arg if trailing ws */
            continue;
        }
        if (c == '\\')
            ++nb;   /* count \'s */
        else {
            if (c == '"') {
                if (!(nb & 1)) { iq = !iq; c = 0; }  /* skip " unless odd # of \ */
                nb = nb >> 1;   /* cut \'s in half */
            }
            while (nb) {*output++ = '\\'; nb--; }
            if (c) *output++ = c;
        }
    } while (1);
}




int run(int argc, char **argv, int is_gui) {

    char python[256];   /* python executable's filename*/
    char *pyopt;        /* Python option */
    char script[256];   /* the script's filename */

    int scriptf;        /* file descriptor for script file */

    char **newargs, **newargsp, **parsedargs; /* argument array for exec */
    char *ptr, *end;    /* working pointers for string manipulation */
    int i, parsedargc;              /* loop counter */

    /* compute script name from our .exe name*/
    GetModuleFileName(NULL, script, sizeof(script));
    end = script + strlen(script);
    while( end>script && *end != '.')
        *end-- = '\0';
    *end-- = '\0';
    strcat(script, (GUI ? "-script.pyw" : "-script.py"));

    /* figure out the target python executable */

    scriptf = open(script, O_RDONLY);
    if (scriptf == -1) {
        return fail("Cannot open %s\n", script);
    }
    end = python + read(scriptf, python, sizeof(python));
    close(scriptf);

    ptr = python-1;
    while(++ptr < end && *ptr && *ptr!='\n' && *ptr!='\r') {;}

    *ptr-- = '\0';

    if (strncmp(python, "#!", 2)) {
        /* default to python.exe if no #! header */
        strcpy(python, "#!python.exe");
    }

    parsedargs = parse_argv(python+2, &parsedargc);

    /* Using spawnv() can fail strangely if you e.g. find the Cygwin
       Python, so we'll make sure Windows can find and load it */

    ptr = find_exe(parsedargs[0], script);
    if (!ptr) {
        return fail("Cannot find Python executable %s\n", parsedargs[0]);
    }

    /* printf("Python executable: %s\n", ptr); */

    /* Argument array needs to be
       parsedargc + argc, plus 1 for null sentinel */

    newargs = (char **)calloc(parsedargc + argc + 1, sizeof(char *));
    newargsp = newargs;

    *newargsp++ = quoted(ptr);
    for (i = 1; i<parsedargc; i++) *newargsp++ = quoted(parsedargs[i]);

    *newargsp++ = quoted(script);
    for (i = 1; i < argc; i++)     *newargsp++ = quoted(argv[i]);

    *newargsp++ = NULL;

    /* printf("args 0: %s\nargs 1: %s\n", newargs[0], newargs[1]); */

    if (is_gui) {
        /* Use exec, we don't need to wait for the GUI to finish */
        execv(ptr, (const char * const *)(newargs));
        return fail("Could not exec %s", ptr);   /* shouldn't get here! */
    }

    /* We *do* need to wait for a CLI to finish, so use spawn */
    return spawnv(P_WAIT, ptr, (const char * const *)(newargs));
}


int WINAPI WinMain(HINSTANCE hI, HINSTANCE hP, LPSTR lpCmd, int nShow) {
    return run(__argc, __argv, GUI);
}

