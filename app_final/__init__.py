from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__,
        static_folder='../static',
        static_url_path='/static',
        template_folder='../templates'  # 同样添加模板文件夹路径
    )
    CORS(app)


    from .api.auth_api import auth_bp
    from .api.recommendation import recommendation_bp


    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(recommendation_bp, url_prefix='/api')


    @app.route('/test')
    def test():
        return "Flask is working!"

    return app