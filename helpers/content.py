# coding=utf-8
from __future__ import absolute_import

from flask import current_app, g
import os
import re
import markdown
from utils.validators import url_validator
from utils.misc import parse_int


def find_content_file(path, default_type=u'page'):
    content_type_slug = path.get('content_type', default_type)
    for file in g.files:
        if file['slug'] == path['slug'] \
           and file['content_type'] == content_type_slug:
            return file
    return None


def query_content_files(attrs, sortby, limit, offset, priority):



def count_content_files(attrs):
    pass


def parse_content(content_string):
    use_markdown = current_app.config.get("USE_MARKDOWN")
    if use_markdown:
        markdown_exts = current_app.config.get("MARKDOWN_EXTENSIONS", [])
        return markdown.markdown(content_string, markdown_exts)
    else:
        return content_string


def get_menus(config):
    menus = config['SITE'].get("menus", {})
    base_url = config.get("BASE_URL")

    def process_menu_url(menu):
        for item in menu:
            link = item.get("link", "")
            if not link or url_validator(link):
                item["url"] = link
            elif link.startswith('/'):
                item["url"] = os.path.join(base_url, link.strip('/'))
            else:
                item["url"] = link.rstrip('/')
            item["nodes"] = process_menu_url(item.get("nodes", []))
        return menu

    for menu in menus:
        menus[menu] = process_menu_url(menus[menu])
    return menus


def get_taxonomies(config):
    taxs = config['SITE'].get("taxonomies", {})
    tax_dict = {}
    for k, v in taxs.iteritems():
        tax_dict[k] = {
            "title": v.get("title"),
            "slug": k,
            "content_types": v.get("content_types"),
            "terms": [
                {
                    "key": x.get("key", u''),
                    "title": x.get("title", u''),
                    "class": x.get("class", u''),
                    "meta": x.get("meta", {}),
                    "nodes": x.get("nodes", []),
                }
                for x in v.get("terms", [])
            ]
        }

    return tax_dict


def read_page_metas(page, content, options, current_id=None):
    config = current_app.config
    excerpt = make_file_excerpt(excerpt)

    data = dict()
    meta = page.get("meta")
    for m in meta:
        data[m] = meta[m]
    data["id"] = page['_id']
    data["app_id"] = page['app_id']
    data["slug"] = page['slug']
    data['type'] = data['content_type'] = page['content_type']
    data["updated"] = page["updated"]
    data["creation"] = page["creation"]

    data['parent'] = meta.get('parent', u'')
    data["priority"] = meta.get("priority", 0)
    data['status'] = meta.get('status', 1)
    data["date"] = meta.get("date", u"")

    data["template"] = meta.get("template", config.get('DEFAULT_INDEX_SLUG'))
    data['taxonomy'] = meta.get('taxonomy', {})
    data['tags'] = meta.get('tags', [])

    excerpt_len = options.get('excerpt_length')
    ellipsis = options.get('excerpt_ellipsis')
    data["excerpt"] = gen_file_excerpt(excerpt, excerpt_len, ellipsis)

    data["description"] = meta.get("description") or data["excerpt"]
    data["url"] = gen_page_url(page['content_type'], page['slug'])

    # content marks
    if data["slug"] == config.get("DEFAULT_INDEX_SLUG"):
        data["is_front"] = True
    if data["slug"] == config.get("DEFAULT_404_SLUG"):
        data["is_404"] = True
    if unicode(data['id']) == unicode(current_id):
        data['is_current'] = True

    return data


def gen_page_url(content_type_slug, file_slug):
    return "{}/{}/{}".format(g.curr_base_url, content_type_slug, file_slug)


def make_file_excerpt(content, length=600):
    excerpt = re.sub(r'<[^>]*?>', '', content).strip()
    return excerpt[:length].strip()


def gen_file_excerpt(excerpt, excerpt_length, ellipsis):
    excerpt_length = parse_int(excerpt_length, 162, True)
    if isinstance(ellipsis, basestring):
        excerpt_ellipsis = ellipsis
    else:
        excerpt_ellipsis = u'&hellip;'

    if excerpt:
        excerpt = u" ".join(excerpt.split())  # remove empty strings.
        excerpt = u"{}{}".format(excerpt[0:excerpt_length], excerpt_ellipsis)
    return excerpt


# menus
def helper_wrap_menu(menus, base_url):
    if not menus:
        return {}

    def process_menu_url(menu):
        for item in menu:
            link = item.get("link", "")
            if not link or url_validator(link):
                item["url"] = link
            elif link.startswith('/'):
                item["url"] = "{}/{}".format(base_url, link.strip('/'))
            else:
                item["url"] = link.rstrip('/')
            item["nodes"] = process_menu_url(item.get("nodes", []))
        return menu

    menu_dict = {}
    for menu in menus:
        nodes = menu.get("nodes", [])
        nodes = process_menu_url(nodes)
        menu_dict[menu.get("slug")] = nodes

    return menu_dict


# socials
def helper_wrap_socials(socials):
    """ socials json sample
    {
       "facebook":{
           "name":"Facebook",
           "url":"http://....",
           "code":"..."
       },
       "twitter":{
           "name":"Twitter",
           "url":"http://....",
           "code":"..."
       }
    }
    """
    if not socials:
        return []

    social_list = []

    if isinstance(socials, list):
        # directly append if is list
        social_list = [social for social in socials if social.get('key')]

    elif isinstance(socials, dict):
        # change to list if is dict
        def _make_key(k, v):
            v.update({"key": k})
            return v
        social_list = [_make_key(k, v) for k, v in socials.iteritems()]

    return social_list


# query contents
def count_matched(attrs):
    pass


# taxonomy
def helper_wrap_taxonomy(taxonomies):
    if not taxonomies:
        return {}

    tax_dict = {}

    def _parse_term(term, tax, content_types):
        attrs = [
            {'type': content_types},
            {'taxonomy.{}'.format(tax["slug"]): term.get('key')}
        ]
        term['count'] = count_matched(attrs)
        return term

    for tax in taxonomies:
        content_types = tax.get("content_types", [])
        tax_dict[tax["slug"]] = {
            "title": tax.get("title"),
            "content_types": content_types,
            "terms": [_parse_term(term, tax, content_types)
                      for term in tax['terms']]
        }
    return tax_dict


# translates
def helper_wrap_translates(translates, locale):
    """ translates json sample
    {
       "zh_CN":{"name":"汉语","url":"http://....."},
       "en_US":{"name":"English","url":"http://....."}
    }
    """
    if not translates:
        return []

    trans_list = []
    lang = locale.split('_')[0]

    if isinstance(translates, list):
        # directly append if is list
        trans_list = [trans for trans in translates if trans.get('key')]

    elif isinstance(translates, dict):
        # change to list if is dict
        def _make_key(k, v):
            v.update({"key": k})
            return v
        trans_list = [_make_key(k, v) for k, v in translates.iteritems()]

    for trans in trans_list:
        trans_key = trans['key'].lower()
        if trans_key == locale.lower() or trans_key == lang.lower():
            trans["active"] = True

    return trans_list
