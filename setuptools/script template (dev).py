# EASY-INSTALL-DEV-SCRIPT: %(spec)r,%(script_name)r
__requires__ = """%(spec)r"""
from pkg_resources import require; require("""%(spec)r""")
del require
__file__ = """%(dev_path)r"""
execfile(__file__)
