"""
Create a release on GitHub Actions from a tag. Invokes bumpversion.
"""

__requires__ = ["bump2version"]

import argparse
import json
import os
from urllib.request import Request, urlopen

from finalize import get_version


def create_release(repo, tag):
    """
    Call the GitHub API to create a release from a tag.
    """
    token = os.environ["GITHUB_TOKEN"]

    _json = json.loads(
        urlopen(
            Request(
                "https://api.github.com/repos/" + repo + "/releases",
                json.dumps({"tag_name": tag, "name": tag}).encode(),
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "Authorization": "token " + token,
                },
            )
        )
        .read()
        .decode()
    )
    print("Released to", _json["html_url"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a release on GitHub Actions from a tag.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "repo", nargs="?", default="pypa/setuptools", help="Repo to release to"
    )
    parser.add_argument(
        "tag", nargs="?", default="v" + get_version(), help="Tag to release"
    )
    args = parser.parse_args()

    print("Creating release", args.tag, "at", args.repo)
    create_release(args.repo, args.tag)
