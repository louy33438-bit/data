#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小鱼智能数据分析处理系统
数据模型模块
"""

from datetime import datetime
from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """
    用户模型
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'


class RawData(db.Model):
    """
    原始数据模型
    """
    __tablename__ = 'raw_data'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)
    title = db.Column(db.String(500), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    content = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<RawData {self.id}: {self.title}>'


class ReportData(db.Model):
    """
    报告数据模型
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_raw_data = db.Column(db.String(500), nullable=True)  # 存储关联的原始数据ID
    
    def __repr__(self):
        return f'<ReportData {self.id}: {self.title}>'