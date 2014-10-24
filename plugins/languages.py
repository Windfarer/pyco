#coding=utf-8
from __future__ import absolute_import
import gettext, os
from flask import current_app

_DEFAULT_LOCALE = 'en'
_TRANSLATE_REDIRECT = False
_LOCALE = None
_TRANSLATES = {}
_current_lang = None
_LANGUAGES_FOLDER = 'languages'
_THEME_NAME = None

def config_loaded(config):
    global _LOCALE, _TRANSLATES, _THEME_NAME
    site_meta = config.get("SITE_META",{})
    theme_meta = config.get("THEME_META",{})
    _THEME_NAME = theme_meta.get("theme_name")
    _LOCALE = site_meta.get("locale", _DEFAULT_LOCALE)
    _TRANSLATES = site_meta.get("translates")
    return

def request_url(request, redirect_to):
    if _TRANSLATES:
        global _current_lang
        _current_lang = request.accept_languages.best_match(_TRANSLATES.keys())
        print request.accept_languages
        print _current_lang
    return

def before_render(var,template):
    if _TRANSLATES:
        set_current_language(_LOCALE)
        current_trans = _TRANSLATES[_current_lang]
        translates = []
        for trans in _TRANSLATES:
            tmp_trans = _TRANSLATES[trans]
            tmp_trans.update({"code":trans})
            translates.append(tmp_trans)
        
        var["translates"] = translates
        var["language_text"] = current_trans["text"]
    
    var["locale"] = _LOCALE
    return

#custome functions
def set_current_language(lang):
    if _TRANSLATES and _THEME_NAME:
        gettext.install(_THEME_NAME,'languages',unicode=True)
        lang_path = os.path.join(current_app.template_folder,_LANGUAGES_FOLDER)
        tr = gettext.translation(_THEME_NAME, lang_path, languages=[lang], fallback=False)
        tr.install(True)
        current_app.jinja_env.install_gettext_translations(tr)