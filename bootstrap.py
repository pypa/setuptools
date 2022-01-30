import warnings


msg = "bootstrap.py is no longer needed. Use a PEP-517-compatible builder instead."


__name__ == '__main__' and warnings.warn(msg)
