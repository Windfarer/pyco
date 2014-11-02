#coding=utf-8
from __future__ import absolute_import
from flask import make_response


def load_config(app, config_name="config.py"):
    app.config.from_pyfile(config_name)
    app.config.setdefault("AUTO_INDEX", False)
    app.config.setdefault("DEBUG", False)
    app.config.setdefault("SITE_INDEX_URL", "/")
    app.config.setdefault("SITE_TITLE", "Pyco Site")
    app.config.setdefault("BASE_URL", "/")
    app.config.setdefault("PLUGINS", [])
    app.config.setdefault("IGNORE_FILES", [])
    app.config.setdefault("THEME_NAME", "default")
    app.config.setdefault("PAGE_DATE_FORMAT", "%d, %b %Y")
    app.config.setdefault("PAGE_ORDER_BY", "title")
    app.config.setdefault("PAGE_ORDER", "asc")
    return


def make_content_response(output, status_code, etag=None):
    response = make_response(output, status_code)
    response.cache_control.public = "public"
    response.cache_control.max_age = 600
    if etag is not None:
        response.set_etag(etag)
    return response