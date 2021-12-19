"""'In-tree' sphinx extension to add icons/favicons to documentation"""
import os
from sphinx.util.fileutil import copy_asset_file


IMAGES_DIR = "_images"  # same used by .. image:: and .. picture::


def _prepare_image(pathto, confdir, outdir, icon_attrs):
    """Copy icon files to the ``IMAGES_DIR`` and return a modified version of
    the icon attributes dict replacing ``file`` with the correct ``href``.
    """
    icon = icon_attrs.copy()
    src = os.path.join(confdir, icon.pop("file"))
    if not os.path.exists(src):
        raise FileNotFoundError(f"icon {src!r} not found")

    dest = os.path.join(outdir, IMAGES_DIR)
    copy_asset_file(src, dest)  # already compares if dest exists and is uptodate

    asset_name = os.path.basename(src)
    icon["href"] = pathto(f"{IMAGES_DIR}/{asset_name}", resource=True)
    return icon


def _link_tag(attrs):
    return "<link " + " ".join(f'{k}="{v}"' for k, v in attrs.items()) + "/>"


def _add_icons(app, _pagename, _templatename, context, doctree):
    """Add multiple "favicons", not limited to PNG/ICO files"""
    # https://evilmartians.com/chronicles/how-to-favicon-in-2021-six-files-that-fit-most-needs
    # https://caniuse.com/link-icon-svg
    try:
        pathto = context['pathto']
    except KeyError as ex:
        msg = f"{__name__} extension is supposed to be call in HTML contexts"
        raise ValueError(msg) from ex

    if doctree and "icons" in app.config:
        icons = [
            _prepare_image(pathto, app.confdir, app.outdir, icon)
            for icon in app.config["icons"]
        ]
        context["metatags"] += "\n".join(_link_tag(attrs) for attrs in icons)


def setup(app):
    images_dir = os.path.join(app.outdir, IMAGES_DIR)
    os.makedirs(images_dir, exist_ok=True)

    app.add_config_value("icons", None, "html")
    app.connect("html-page-context", _add_icons)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
