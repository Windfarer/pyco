# coding=utf-8
from __future__ import absolute_import

from flask import current_app, request, abort, render_template, redirect, g
import os

from services.i18n import Translator
from utils.request import parse_args
from utils.response import make_content_response
from utils.misc import make_dotted_dict
from helpers.app import (run_hook,
                         helper_get_statistic,
                         helper_redirect_url,
                         get_theme_path,
                         get_theme_abs_path)
from helpers.content import (content_splitter,
                             helper_get_file_path,
                             helper_wrap_socials,
                             helper_wrap_translates,
                             helper_wrap_menu,
                             helper_wrap_taxonomy,
                             get_pages,
                             parse_file_headers,
                             parse_file_metas,
                             parse_content)


def get_content(content_type_slug='page', file_slug='index'):
    config = current_app.config
    charset = config.get('CHARSET')
    default_404_slug = config.get("DEFAULT_404_SLUG")

    base_url = g.curr_base_url
    curr_app = g.curr_app
    site_meta = curr_app['site_meta']
    theme_meta = curr_app['theme_meta']
    theme_options = theme_meta.get('options', {})

    run_hook("config_loaded", config=config)

    if file_slug == default_404_slug:
        status_code = 404
    else:
        status_code = 200

    # hidden content types
    if _check_theme_hidden_types(theme_meta, content_type_slug):
        redirect_url = helper_redirect_url(default_404_slug, base_url)
        return redirect(redirect_url, code=302)

    run_hook("request_url", request=request)

    view_ctx = dict()

    # find file path
    file = {"path": None}
    file["path"] = helper_get_file_path(file_slug, content_type_slug)

    run_hook("before_load_content", file=file)

    # if not found
    if file["path"] is None:
        status_code = 404
        file["path"] = _find_404_path()
        run_hook("before_404_load_content", file=file)
        if not file["path"]:
            abort(404)  # without not found 404 file
            return

    # load file content
    file_content = {"content": None}
    with open(file['path'], "r") as f:
        file_content['content'] = f.read().decode(charset)

    if status_code == 404:
        run_hook("after_404_load_content", file=file, content=file_content)

    run_hook("after_load_content", file=file, content=file_content)

    # parse file content
    tmp_file_content = file_content["content"]
    meta_string, content_string = content_splitter(tmp_file_content)

    meta_string = {"meta": meta_string}
    run_hook("before_read_page_meta", meta_string=meta_string)
    try:
        headers = parse_file_headers(meta_string['meta'])
    except Exception as e:
        raise Exception("{}: {}".format(str(e), file["path"]))

    run_hook("after_read_page_meta", headers=headers)

    page_meta = parse_file_metas(headers,
                                 file["path"],
                                 content_string,
                                 theme_options)
    redirect_to = {"url": None}
    run_hook("single_page_meta", page_meta=page_meta, redirect_to=redirect_to)

    # page redirect
    if redirect_to["url"]:
        redirect_to = helper_redirect_url(redirect_to["url"], base_url)
        if redirect_to and request.url != redirect_to:
            return redirect(redirect_to["url"], code=302)

    view_ctx["meta"] = page_meta

    # content
    page_content = dict()
    page_content['content'] = content_string
    run_hook("before_parse_content", content=page_content)

    page_content['content'] = parse_content(page_content['content'])
    run_hook("after_parse_content", content=page_content)

    view_ctx["content"] = page_content['content']

    # site_meta
    site_meta = curr_app["meta"]
    site_meta['title'] = curr_app["title"]
    site_meta['description'] = curr_app["description"]
    site_meta['slug'] = curr_app['slug']
    site_meta["id"] = curr_app["id"]
    site_meta["type"] = curr_app['type']
    site_meta["visit"] = helper_get_statistic(curr_app['id'], page_meta['id'])

    # extension slots
    ext_slots = curr_app_extension["slots"] or {}
    for k, v in ext_slots.iteritems():
        ext_slots[k] = helper_render_ext_slots(v, curr_app)
    view_context["slot"] = ext_slots

    # base view context
    view_ctx["app_id"] = curr_app["id"]
    view_ctx["api_baseurl"] = current_app.config.get('API_URL', u'')
    view_ctx["site_meta"] = make_dotted_dict(site_meta)
    view_ctx["theme_meta"] = make_dotted_dict(theme_meta)
    view_ctx["theme_url"] = theme_url
    view_ctx["libs_url"] = current_app.config.get("LIBS_URL", u'')
    view_ctx["base_url"] = curr_base_url

    # request
    view_ctx["request"] = {
        "remote_addr": g.request_remote_addr,
        "path": g.request_path,
        "url": g.request_url,
        "args": parse_args(),
    }
    view_ctx["args"] = view_ctx["request"]["args"]

    # multi-language support
    set_multi_language(view_ctx, curr_app)

    # soical media support
    view_ctx["socials"] = helper_wrap_socials(curr_app['socials'])

    # menu
    view_ctx["menu"] = helper_wrap_menu(curr_app['menus'], base_url)

    # taxonomy
    view_ctx["taxonomy"] = helper_wrap_taxonomy(curr_app)

    # pages
    pages = get_pages()
    for p in pages:
        run_hook("get_page_data", data=p)
    run_hook("get_pages", pages=pages, current_page=page_meta)
    view_ctx["pages"] = pages

    # template
    template = dict()
    template['file'] = page_meta.get("template")
    run_hook("before_render", var=view_ctx, template=template)

    template_file_path = get_theme_path(template['file'])
    template_file_abs_path = get_theme_abs_path(template_file_path)

    if not os.path.isfile(template_file_abs_path):
        template['file'] = None
        default_template = config.get('DEFAULT_TEMPLATE')
        template_file_path = get_theme_path(default_template)

    # make dotted able
    for k, v in view_ctx.iteritems():
        view_ctx[k] = make_dotted_dict(v)

    output = {}
    output['content'] = render_template(template_file_path, **view_ctx)
    run_hook("after_render", output=output)

    return make_content_response(output['content'], status_code)


def _check_theme_hidden_types(theme_meta, curr_type):
    if curr_type == 'page':
        return False
    cfg_types = theme_meta.get('content_types', {})
    status_type = cfg_types.get(curr_type, {}).get('status', 1)
    return status_type == 0


def _find_404_path():
    content_dir = current_app.config.get('CONTENT_DIR')
    file_404 = "{}{}".format(current_app.config.get('DEFAULT_404_SLUG'),
                             current_app.config.get('CONTENT_FILE_EXT'))
    file_404_path = os.path.join(content_dir, file_404)
    if not os.path.isfile(file_404_path):
        file_404_path = None
    return file_404_path


def set_multi_language(view_context, app):
    locale = app['locale']
    # make i18n support
    lang_dir = current_app.config.get('LANGUAGES_DIR', 'languages')
    lang_path = os.path.join(current_app.template_folder, lang_dir)
    translator = Translator(locale, lang_path)
    view_context['_'] = translator.gettext
    view_context['_t'] = translator.t_gettext
    view_context["locale"] = locale
    view_context["lang"] = locale.split('_')[0]
    # make translates
    trans_list = helper_wrap_translates(app['translates'], locale)
    view_context["translates"] = make_dotted_dict(trans_list)
