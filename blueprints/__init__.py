# coding=utf-8
from __future__ import absolute_import
# from .tradition import blueprint as tradition_module


def register_blueprints(app):
    # register tradition
    # app.register_blueprint(tradition_module)

    # register uploads
    from .uploads import blueprint as uploads_module
    uploads_dir = app.config.get('UPLOADS_DIR')
    app.register_blueprint(uploads_module,
                           url_prefix="/{}".format(uploads_dir))