#!/usr/bin/env python
# -*- coding: utf-8 -*-

# declare and require dependencies
__requires__ = [
    'twine',
]; __import__('pkg_resources')

import errno
import glob
import hashlib
import json
import os
import shutil
import tarfile
import codecs
import urllib.request
import urllib.parse
import urllib.error
from distutils.version import LooseVersion

from twine.commands import upload


OK = '\033[92m'
FAIL = '\033[91m'
END = '\033[0m'
DISTRIBUTION = "setuptools"


class SetuptoolsOldReleasesWithoutZip:
    """docstring for SetuptoolsOldReleases"""

    def __init__(self):
        self.dirpath = './dist'
        os.makedirs(self.dirpath, exist_ok=True)
        print("Downloading %s releases..." % DISTRIBUTION)
        print("All releases will be downloaded to %s" % self.dirpath)
        self.data_json_setuptools = self.get_json_data(DISTRIBUTION)
        self.valid_releases_numbers = sorted([
            release
            for release in self.data_json_setuptools['releases']
            # This condition is motivated by 13.0 release, which
            # comes as "13.0": [], in the json
            if self.data_json_setuptools['releases'][release]
        ], key=LooseVersion)
        self.total_downloaded_ok = 0

    def get_json_data(self, package_name):
        """
        "releases": {
            "0.7.2": [
                {
                    "has_sig": false,
                    "upload_time": "2013-06-09T16:10:00",
                    "comment_text": "",
                    "python_version": "source",
                    "url": "https://pypi.python.org/packages/source/s/setuptools/setuptools-0.7.2.tar.gz",  # NOQA
                    "md5_digest": "de44cd90f8a1c713d6c2bff67bbca65d",
                    "downloads": 159014,
                    "filename": "setuptools-0.7.2.tar.gz",
                    "packagetype": "sdist",
                    "size": 633077
                }
            ],
            "0.7.3": [
                {
                    "has_sig": false,
                    "upload_time": "2013-06-18T21:08:56",
                    "comment_text": "",
                    "python_version": "source",
                    "url": "https://pypi.python.org/packages/source/s/setuptools/setuptools-0.7.3.tar.gz",  # NOQA
                    "md5_digest": "c854adacbf9067d330a847f06f7a8eba",
                    "downloads": 30594,
                    "filename": "setuptools-0.7.3.tar.gz",
                    "packagetype": "sdist",
                    "size": 751152
                }
            ],
            "12.3": [
                {
                    "has_sig": false,
                    "upload_time": "2015-02-26T19:15:51",
                    "comment_text": "",
                    "python_version": "3.4",
                    "url": "https://pypi.python.org/packages/3.4/s/setuptools/setuptools-12.3-py2.py3-none-any.whl",  # NOQA
                    "md5_digest": "31f51a38497a70efadf5ce8d4c2211ab",
                    "downloads": 288451,
                    "filename": "setuptools-12.3-py2.py3-none-any.whl",
                    "packagetype": "bdist_wheel",
                    "size": 501904
                },
                {
                    "has_sig": false,
                    "upload_time": "2015-02-26T19:15:43",
                    "comment_text": "",
                    "python_version": "source",
                    "url": "https://pypi.python.org/packages/source/s/setuptools/setuptools-12.3.tar.gz",  # NOQA
                    "md5_digest": "67614b6d560fa4f240e99cd553ec7f32",
                    "downloads": 110109,
                    "filename": "setuptools-12.3.tar.gz",
                    "packagetype": "sdist",
                    "size": 635025
                },
                {
                    "has_sig": false,
                    "upload_time": "2015-02-26T19:15:47",
                    "comment_text": "",
                    "python_version": "source",
                    "url": "https://pypi.python.org/packages/source/s/setuptools/setuptools-12.3.zip",  # NOQA
                    "md5_digest": "abc799e7db6e7281535bf342bfc41a12",
                    "downloads": 67539,
                    "filename": "setuptools-12.3.zip",
                    "packagetype": "sdist",
                    "size": 678783
                }
            ],
        """
        url = "https://pypi.python.org/pypi/%s/json" % (package_name,)
        resp = urllib.request.urlopen(urllib.request.Request(url))
        charset = resp.info().get_content_charset()
        reader = codecs.getreader(charset)(resp)
        data = json.load(reader)

        # Mainly for debug.
        json_filename = "%s/%s.json" % (self.dirpath, DISTRIBUTION)
        with open(json_filename, 'w') as outfile:
            json.dump(
                data,
                outfile,
                sort_keys=True,
                indent=4,
                separators=(',', ': '),
            )

        return data

    def get_setuptools_releases_without_zip_counterpart(self):
        # Get set(all_valid_releases) - set(releases_with_zip), so now we have
        # the releases without zip.
        return set(self.valid_releases_numbers) - set([
            release
            for release in self.valid_releases_numbers
                for same_version_release_dict in self.data_json_setuptools['releases'][release]  # NOQA
                if 'zip' in same_version_release_dict['filename']
       ])

    def download_setuptools_releases_without_zip_counterpart(self):
        try:
            releases_without_zip = self.get_setuptools_releases_without_zip_counterpart()  # NOQA
            failed_md5_releases = []
            # This is a "strange" loop, going through all releases and
            # testing only the release I need to download, but I thought it
            # would be mouch more readable than trying to iterate through
            # releases I need and get into traverse hell values inside dicts
            # inside dicts of the json to get the distribution's url to
            # download.
            for release in self.valid_releases_numbers:
                if release in releases_without_zip:
                    for same_version_release_dict in self.data_json_setuptools['releases'][release]:  # NOQA
                        if 'tar.gz' in same_version_release_dict['filename']:
                            print("Downloading %s..." % release)
                            local_file = '%s/%s' % (
                                self.dirpath,
                                same_version_release_dict["filename"]
                            )
                            urllib.request.urlretrieve(
                                same_version_release_dict["url"],
                                local_file
                            )
                            targz = open(local_file, 'rb').read()
                            hexdigest = hashlib.md5(targz).hexdigest()
                            if (hexdigest != same_version_release_dict['md5_digest']):  # NOQA
                                print(FAIL + "FAIL: md5 for %s didn't match!" % release + END)  # NOQA
                                failed_md5_releases.append(release)
                            else:
                                self.total_downloaded_ok += 1
            print('Total releases without zip: %s' % len(releases_without_zip))
            print('Total downloaded: %s' % self.total_downloaded_ok)
            if failed_md5_releases:
                msg = FAIL + (
                    "FAIL: these releases %s failed the md5 check!" %
                    ','.join(failed_md5_releases)
                ) + END
                raise Exception(msg)
            elif self.total_downloaded_ok != len(releases_without_zip):
                msg = FAIL + (
                    "FAIL: Unknown error occured. Please check the logs."
                ) + END
                raise Exception(msg)
            else:
                print(OK + "All releases downloaded and md5 checked." + END)

        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    @staticmethod
    def version_from_filename(filename):
        basename = os.path.basename(filename)
        name, ext = os.path.splitext(basename)
        if name.endswith('.tar'):
            name, ext2 = os.path.splitext(name)
        return LooseVersion(name)

    def convert_targz_to_zip(self):
        print("Converting the tar.gz to zip...")
        files = glob.glob('%s/*.tar.gz' % self.dirpath)
        total_converted = 0
        for targz in sorted(files, key=self.version_from_filename):
            # Extract and remove tar.
            tar = tarfile.open(targz)
            tar.extractall(path=self.dirpath)
            tar.close()
            os.remove(targz)

            # Zip the extracted tar.
            setuptools_folder_path = targz.replace('.tar.gz', '')
            setuptools_folder_name = setuptools_folder_path.split("/")[-1]
            print(setuptools_folder_name)
            shutil.make_archive(
                setuptools_folder_path,
                'zip',
                self.dirpath,
                setuptools_folder_name
            )
            # Exclude extracted tar folder.
            shutil.rmtree(setuptools_folder_path.replace('.zip', ''))
            total_converted += 1
        print('Total converted: %s' % total_converted)
        if self.total_downloaded_ok != total_converted:
            msg = FAIL + (
                "FAIL: Total number of downloaded releases is different"
                " from converted ones. Please check the logs."
            ) + END
            raise Exception(msg)
        print("Done with the tar.gz->zip. Check folder %s." % main.dirpath)

    def upload_zips_to_pypi(self):
        print('Uploading to pypi...')
        zips = sorted(glob.glob('%s/*.zip' % self.dirpath), key=self.version_from_filename)
        upload.upload(
            dists=zips,
            repository='pypi',
            sign=False,
            identity=None,
            username=None,
            password=None,
            comment=None,
            sign_with='gpg',
            config_file='~/.pypirc',
            skip_existing=False,
        )


if __name__ == '__main__':
    main = SetuptoolsOldReleasesWithoutZip()
    main.download_setuptools_releases_without_zip_counterpart()
    main.convert_targz_to_zip()
    main.upload_zips_to_pypi()
