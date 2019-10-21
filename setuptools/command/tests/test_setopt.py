import pytest
from collections import OrderedDict

from setuptools.command import setopt


@pytest.fixture()
def config_path(tmpdir):
    config_dir = tmpdir.mkdir('config_dir')
    return str(config_dir.join('setup.cfg'))


def check(config_path, expected):
    with open(config_path) as f:
        config = f.read().strip()
    assert config == expected


def test_empty(config_path):
    setopt.edit_config(
        config_path,
        {}
    )
    expected = ''
    check(config_path, expected)


def test_empty_section(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('easy_install', {})
        ])
    )
    expected = "[easy_install]"
    check(config_path, expected)


def test_section_with_one_recond(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('easy_install', OrderedDict([
                ('index-url', 'some_url'),
            ]))
        ])
    )
    expected = "[easy_install]\nindex-url = some_url"
    check(config_path, expected)


def test_section_with_one_list_recond(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('easy_install', OrderedDict([
                ('find-links', ['some_url', 'another_url']),
            ]))
        ])
    )
    expected = "[easy_install]\nfind-links = some_url\n\tanother_url"
    check(config_path, expected)


def test_section_with_two_recond(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('easy_install', OrderedDict([
                ('index-url', 'some_url'),
                ('find-links', 'other_url'),
            ]))
        ])
    )
    expected = "[easy_install]\nindex-url = some_url\nfind-links = other_url"
    check(config_path, expected)


def test_delete_section(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('pls_remove_me', {}),
            (
                'keep_this_section',
                OrderedDict([
                    ('keep_this_option', 'keep_this_value')
                ])
            ),
        ])
    )
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('pls_remove_me', None),
        ])
    )
    expected = "[keep_this_section]\nkeep_this_option = keep_this_value"
    check(config_path, expected)


def test_delete_option(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            (
                'keep_this_section',
                OrderedDict([
                    ('keep_this_option', 'keep_this_value'),
                    ('pls_remove_me', 'some_value')
                ])
            ),
        ])
    )
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('keep_this_section', {
                'pls_remove_me': None
            }),
        ])
    )
    expected = "[keep_this_section]\nkeep_this_option = keep_this_value"
    check(config_path, expected)


def test_delete_the_last_option(config_path):
    setopt.edit_config(
        config_path,
        OrderedDict([
            (
                'pls_remove_this_section',
                OrderedDict([
                    ('pls_remove_me', 'some_value')
                ])
            ),
            (
                'keep_me',
                OrderedDict([
                    ('keep_me_too', 'some_value')
                ])
            ),
        ])
    )
    setopt.edit_config(
        config_path,
        OrderedDict([
            ('pls_remove_this_section', {
                'pls_remove_me': None
            }),
        ])
    )
    expected = "[keep_me]\nkeep_me_too = some_value"
    check(config_path, expected)
