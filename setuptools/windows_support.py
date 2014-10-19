import ctypes


def hide_file(path):
    """
    Set the hidden attribute on a file or directory.

    From http://stackoverflow.com/questions/19622133/

    `path` must be text.
    """

    SetFileAttributesW = ctypes.windll.kernel32.SetFileAttributesW

    FILE_ATTRIBUTE_HIDDEN = 0x02

    ret = SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)
    if not ret:
        raise ctypes.WinError()
