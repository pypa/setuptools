# -*- coding: utf-8 -*-

"""TLS/SSL support tests.
"""


from __future__ import unicode_literals

import pytest
from setuptools import ssl_support


class TestGetEnvCABundle:
    @pytest.mark.parametrize(
        'env_var', ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'])
    def test_get_env_ca_bundle(self, env_var, monkeypatch, tmp_path):
        # Test that get_env_ca_bundle() respects the env variables.
        ca_bundle_path = tmp_path / 'ca-bundle.crt'
        ca_bundle_path_str = str(ca_bundle_path)
        # Create a valid file, content is irrelevant
        ca_bundle_path.write_text('')
        monkeypatch.setenv(env_var, ca_bundle_path_str)
        assert ssl_support.get_env_ca_bundle() == ca_bundle_path_str

    @pytest.mark.parametrize(
        'env_var', ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'])
    def test_get_env_ca_bundle_invalid_file(
            self, env_var, monkeypatch, tmp_path):
        # Test get_env_ca_bundle() behaviour if the given path is not an
        # existing file.
        ca_bundle_path = tmp_path / 'non-existant'
        ca_bundle_path_str = str(ca_bundle_path)
        # Don't create a file!
        monkeypatch.setenv(env_var, ca_bundle_path_str)
        with pytest.raises(IOError):
            _ = ssl_support.get_env_ca_bundle()

    @pytest.mark.parametrize(
        'env_var', ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'])
    def test_get_env_ca_bundle_dir(self, env_var, monkeypatch, tmp_path):
        # Test get_env_ca_bundle() behaviour if the given ca bundle path is a
        # directory (currently unsupported).
        ca_bundle_path = tmp_path / 'ca-bundles'
        ca_bundle_path_str = str(ca_bundle_path)
        ca_bundle_path.mkdir()
        monkeypatch.setenv(env_var, ca_bundle_path_str)
        with pytest.raises(NotImplementedError):
            _ = ssl_support.get_env_ca_bundle()

    @pytest.mark.parametrize(
        'env_variables', [
            ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'),
            ('REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE')])
    def test_get_env_ca_bundle_envvar_precedence(
            self, env_variables, monkeypatch, tmp_path):
        # Test precedence when multiple env vars are set.
        for env_var in env_variables:
            ca_bundle_path = tmp_path / (env_var + '.crt')
            ca_bundle_path_str = str(ca_bundle_path) 
            # Create a valid file, content is irrelevant
            ca_bundle_path.write_text('')
            monkeypatch.setenv(env_var, ca_bundle_path_str)
        expected = str(tmp_path / (env_variables[0] + '.crt'))
        assert ssl_support.get_env_ca_bundle() ==  expected


class TestFindCABundle:
    @pytest.mark.parametrize(
        'env_var', ['SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'])
    def test_find_ca_bundle(self, env_var, monkeypatch, tmp_path):
        ca_bundle_path = tmp_path / 'ca-bundle.crt'
        ca_bundle_path_str = str(ca_bundle_path)
        # Create a valid file, content is irrelevant
        ca_bundle_path.write_text('')
        monkeypatch.setenv(env_var, ca_bundle_path_str)
        assert ssl_support.find_ca_bundle() == ca_bundle_path_str
