# coding=utf8

from types import ModuleType
import re


def load_config(app, config_name='config.py'):
    app.config.from_pyfile(config_name)
    app.config.setdefault('DEBUG', False)
    app.config.setdefault('CONTENT_QUERY_LIMIT', 3)

    app.config.setdefault('PAYLOAD_DIR', 'paylaod')
    app.config.setdefault('BACKUPS_DIR', '_backups')

    app.config.setdefault('THEME_NAME', 'default')

    app.config.setdefault('BASE_URL', '/')
    app.config.setdefault('RES_URL', '')
    app.config.setdefault('UPLOADS_URL', '')
    app.config.setdefault('THEME_URL', '')
    app.config.setdefault('API_URL', '')

    app.config.setdefault('PLUGINS', [])
    app.config.setdefault('SHORTCODE', {})

    app.config.setdefault('HOST', '0.0.0.0')
    app.config.setdefault('PORT', 5500)

    app.config.setdefault('SYS_ICONS', ['favicon.ico',
                                        'apple-touch-icon-precomposed.png',
                                        'apple-touch-icon.png'])

    app.config.setdefault('ADMIN_PORT', 5510)
    app.config.setdefault('ADMIN_BASE_URL', ':5510/')

    app.debug = app.config['DEBUG']


def load_plugins(app):
    plugins = app.config.get('PLUGINS')
    loaded_plugins = []
    for module_or_module_name in plugins:
        if type(module_or_module_name) is ModuleType:
            loaded_plugins.append(module_or_module_name)
        elif isinstance(module_or_module_name, str):
            try:
                module = __import__(module_or_module_name)
            except ImportError as err:
                raise err
            loaded_plugins.append(module)
    app.plugins = loaded_plugins


def load_metas(app):
    site = app.db.Site()
    theme = app.db.Theme(app.config['THEME_NAME'])

    site_meta = site.meta
    theme_meta = theme

    return {
        '_id': site.get('app_id', 'pyco_app'),
        'slug': site.get('slug', 'pyco'),
        'type': site.get('type', 'ws'),
        'locale': site.get('locale', 'en_US'),
        'content_types': site.get('content_types', {'page': 'Pages'}),
        'categories': site.get('categories', None),
        'menus': site.get('menus', None),
        'slots': site.get('slots', None),
        'languages': site_meta.pop('languages', None),
        'site_meta': site_meta,
        'theme_meta': theme_meta
    }


def load_modal_pretreat(app):
    if not isinstance(app.config['SHORTCODE'], dict):
        return None

    def pretreat_raw_method(self, text):
        for code, replace_to in app.config['SHORTCODE'].items():
            try:
                _compiler = re.compile(r'\[\%{}\%\]'.fromat(str(code)),
                                       re.IGNORECASE)
                text = re.sub(_compiler, str(replace_to), str(text))
            except Exception as e:
                app.logger.error('Shortcode Error: {}'.format(e))
        return text
    return pretreat_raw_method
