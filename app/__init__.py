#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小鱼智能数据分析处理系统
应用初始化模块
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 创建数据库实例
db = SQLAlchemy()

# 创建登录管理器实例
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'


def create_app():
    """
    创建Flask应用实例
    """
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 注册蓝图
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        # 创建默认管理员用户
        from app.models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', password='admin888')
            db.session.add(admin)
            db.session.commit()
    
    return app


@login_manager.user_loader
def load_user(user_id):
    """
    用户加载器
    """
    from app.models import User
    return User.query.get(int(user_id))