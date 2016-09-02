# coding=utf-8
from __future__ import absolute_import

from flask import current_app
import os
import re
from hashlib import sha1
from utils.validators import url_validator


def run_hook(hook_name, **references):
    for plugin_module in current_app.plugins:
        func = plugin_module.__dict__.get(hook_name)
        if callable(func):
            func(**references)
    return


def generate_etag(content_file_full_path):
    file_stat = os.stat(content_file_full_path)
    base = "{mtime:0.0f}_{size:d}_{fpath}".format(
        mtime=file_stat.st_mtime,
        size=file_stat.st_size,
        fpath=content_file_full_path
    )

    return sha1(base).hexdigest()


def get_theme_path(tmpl_name):
    return "{}{}".format(tmpl_name,
                         current_app.config.get('TEMPLATE_FILE_EXT'))


def get_theme_abs_path(tmpl_path):
    return os.path.join(current_app.root_path,
                        current_app.template_folder,
                        tmpl_path)


def helper_redirect_url(url, base_url):
    if not url or not isinstance(url, (str, unicode)):
        return None
    if re.match("^(?:http|ftp)s?://", url):
        return url
    else:
        return "{}/{}".format(base_url, url.strip('/'))


# statistic
def helper_get_statistic(app_id, page_id=None):
    sa = {
        'pv': 0,
        'vs': 0,
        'uv': 0,
        'ip': 0,
    }
    if page_id:
        sa['page'] = 0

    return sa