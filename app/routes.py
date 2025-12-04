#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小鱼智能数据分析处理系统
路由和视图模块
"""

import sys
import sys
import json
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, session, make_response
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, RawData, ReportData
import importlib.util
import traceback

# 创建蓝图
main = Blueprint('main', __name__)

# 导入百度爬虫模块
spider_module = None
bilibili_spider_module = None

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)

try:
    # 动态导入baidu_spider.py
    baidu_spider_path = os.path.join(project_root, "baidu_spider.py")
    spec = importlib.util.spec_from_file_location("baidu_spider", baidu_spider_path)
    spider_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(spider_module)
except Exception as e:
    print(f"导入百度爬虫模块失败: {e}")

try:
    # 动态导入bilibili_spider.py
    bilibili_spider_path = os.path.join(project_root, "bilibili_spider.py")
    spec = importlib.util.spec_from_file_location("bilibili_spider", bilibili_spider_path)
    bilibili_spider_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bilibili_spider_module)
except Exception as e:
    print(f"导入B站爬虫模块失败: {e}")


@main.route('/')
def index():
    """
    首页路由
    """
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录路由
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # 简化的密码验证，生产环境应使用哈希
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    """
    注册路由
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('main.register'))
        
        # 验证密码和确认密码是否一致
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('main.register'))
        
        # 创建新用户
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('main.login'))
    
    return render_template('register.html')


@main.route('/logout')
def logout():
    """
    登出路由
    """
    logout_user()
    return redirect(url_for('main.login'))


@main.route('/dashboard')
@login_required
def dashboard():
    """
    后台主页
    """
    return render_template('dashboard.html')


@main.route('/search', methods=['POST'])
@login_required
def search():
    """
    执行搜索，同时调用百度爬虫和B站爬虫
    """
    print("开始处理搜索请求")
    try:
        # 检查请求方法和数据
        if request.method != 'POST':
            return jsonify({'status': 'error', 'message': '请求方法错误'}), 405
        
        # 获取搜索关键词
        if request.is_json:
            data = request.json
            keyword = data.get('keyword', '').strip()
        else:
            keyword = request.form.get('keyword', '').strip()
            
        print(f"接收到的搜索关键词: '{keyword}'")
        
        if not keyword:
            print("搜索关键词为空")
            return jsonify({'status': 'error', 'message': '搜索关键词不能为空'})
        
        # 记录搜索关键词到session中，用于保存数据时使用
        session['last_search_keyword'] = keyword
        
        # 合并结果列表
        all_formatted_results = []
        
        # 严格筛选函数 - 检查结果是否与关键词高度相关
        def is_highly_relevant(result, keyword):
            # 检查标题、摘要是否包含关键词
            title = result.get('title', '').lower()
            summary = result.get('summary', '').lower()
            keyword_lower = keyword.lower()
            
            # 完全匹配或包含关键词作为独立词
            if (keyword_lower in title or keyword_lower in summary or 
                (title.find(f" {keyword_lower} ") != -1) or 
                (summary.find(f" {keyword_lower} ") != -1)):
                return True
            return False

        # 调用百度爬虫 - 限制返回5条高度相关的结果
        baidu_selected = []
        if spider_module:
            print("开始调用百度爬虫")
            try:
                # 首先尝试直接调用模块的search函数
                if hasattr(spider_module, 'search'):
                    baidu_results = spider_module.search(keyword)
                else:
                    # 如果没有直接的search函数，则实例化BaiduSpider类
                    spider = spider_module.BaiduSpider()
                    baidu_results = spider.search(keyword)
                
                print(f"百度爬虫返回了 {len(baidu_results)} 条原始结果")
                
                # 严格筛选百度结果
                for result in baidu_results:
                    if is_highly_relevant(result, keyword):
                        formatted_result = {
                            'title': result.get('title', ''),
                            'url': result.get('url', ''),
                            'summary': result.get('summary', ''),
                            'source': '百度'  # 标记来源为百度
                        }
                        # 添加原始来源信息（如果有）
                        if result.get('source') and result.get('source') != '百度':
                            formatted_result['source'] = f"百度 - {result.get('source')}"
                        baidu_selected.append(formatted_result)
                        # 只保留前5条高度相关的结果
                        if len(baidu_selected) >= 5:
                            break
                
                print(f"百度爬虫筛选后获得 {len(baidu_selected)} 条结果")
                
            except Exception as inner_e:
                error_msg = f"调用百度爬虫失败: {str(inner_e)}"
                print(error_msg)
                print(traceback.format_exc())
        else:
            print("百度爬虫模块未加载")
        
        # 调用B站爬虫 - 限制返回5条高度相关的结果
        bilibili_selected = []
        if bilibili_spider_module:
            print("开始调用B站爬虫")
            try:
                # 首先尝试直接调用模块的search函数
                if hasattr(bilibili_spider_module, 'search'):
                    bilibili_results = bilibili_spider_module.search(keyword)
                else:
                    # 如果没有直接的search函数，则实例化BilibiliSpider类
                    spider = bilibili_spider_module.BilibiliSpider()
                    bilibili_results = spider.search(keyword)
                
                print(f"B站爬虫返回了 {len(bilibili_results)} 条原始结果")
                
                # 严格筛选B站结果
                for result in bilibili_results:
                    if is_highly_relevant(result, keyword):
                        formatted_result = {
                            'title': result.get('title', ''),
                            'url': result.get('url', ''),
                            'summary': result.get('summary', ''),
                            'source': 'Bilibili'  # 标记来源为B站
                        }
                        # 添加UP主信息到摘要中
                        if result.get('author'):
                            if formatted_result['summary']:
                                formatted_result['summary'] = f"UP主: {result.get('author')}\n{formatted_result['summary']}"
                            else:
                                formatted_result['summary'] = f"UP主: {result.get('author')}"
                        # 添加播放数据到摘要中
                        if result.get('stats'):
                            if formatted_result['summary']:
                                formatted_result['summary'] = f"{formatted_result['summary']}\n数据: {result.get('stats')}"
                            else:
                                formatted_result['summary'] = f"数据: {result.get('stats')}"
                        bilibili_selected.append(formatted_result)
                        # 只保留前5条高度相关的结果
                        if len(bilibili_selected) >= 5:
                            break
                
                print(f"B站爬虫筛选后获得 {len(bilibili_selected)} 条结果")
                
            except Exception as inner_e:
                error_msg = f"调用B站爬虫失败: {str(inner_e)}"
                print(error_msg)
                print(traceback.format_exc())
        else:
            print("B站爬虫模块未加载")
        
        # 合并结果
        all_formatted_results = []
        # 先添加百度结果
        all_formatted_results.extend(baidu_selected)
        # 再添加B站结果
        all_formatted_results.extend(bilibili_selected)
        
        print(f"合并后的总结果数: {len(all_formatted_results)}")
        
        # 检查是否有结果
        if not all_formatted_results:
            # 如果两个爬虫都失败，提供更详细的错误信息
            if not spider_module and not bilibili_spider_module:
                print("百度爬虫和B站爬虫模块均未加载")
                return jsonify({'status': 'error', 'message': '百度爬虫和B站爬虫模块均加载失败，请检查爬虫模块是否正确安装'})
            elif not spider_module:
                print("百度爬虫模块未加载，但B站爬虫模块已加载")
                return jsonify({'status': 'error', 'message': '百度爬虫模块加载失败，请检查baidu_spider.py文件'})
            elif not bilibili_spider_module:
                print("B站爬虫模块未加载，但百度爬虫模块已加载")
                return jsonify({'status': 'error', 'message': 'B站爬虫模块加载失败，请检查bilibili_spider.py文件'})
            else:
                print("爬虫模块已加载，但未返回任何结果")
                # 创建一个模拟结果，以便用户可以测试系统功能
                mock_results = [
                    {
                        'title': f'关于"{keyword}"的示例结果',
                        'url': '#',
                        'summary': '这是一个模拟的搜索结果，用于测试系统功能。实际使用时，这里会显示相关的搜索内容。',
                        'source': '百度'
                    }
                ]
                return jsonify({'status': 'success', 'results': mock_results, 'keyword': keyword, 'is_mock': True})
        
        # 成功返回结果
        return jsonify({'status': 'success', 'results': all_formatted_results, 'keyword': keyword})
        
    except Exception as e:
        error_msg = f"搜索过程发生错误: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        # 即使发生错误，也提供一个模拟结果，以便用户可以继续测试
        mock_results = [
            {
                'title': f'关于"{keyword}"的示例结果（系统错误）',
                'url': '#',
                'summary': f'系统在搜索过程中遇到问题: {str(e)}。这是一个替代显示的示例结果。',
                'source': '系统'
            }
        ]
        return jsonify({'status': 'success', 'results': mock_results, 'keyword': keyword, 'is_mock': True, 'error': str(e)})


@main.route('/save_data', methods=['POST'])
@login_required
def save_data():
    """
    批量保存数据到数据库
    """
    print("接收到保存数据请求")
    try:
        # 确保能正确解析JSON数据
        if not request.is_json:
            print("请求不是JSON格式")
            return jsonify({'status': 'error', 'message': '请求数据格式错误，请使用JSON格式'}), 400
        
        data = request.json
        print(f"接收到的数据完整内容: {json.dumps(data, ensure_ascii=False, default=str)}")
        
        # 提取结果和关键词
        results = data.get('results', [])
        keyword = data.get('keyword', '') or session.get('last_search_keyword', '未知')
        print(f"关键词: {keyword}, 结果数量: {len(results)}")
        
        if not results:
            print("没有数据需要保存")
            return jsonify({'status': 'error', 'message': '没有数据需要保存'})
        
        # 批量保存数据
        saved_count = 0
        all_items_valid = True
        
        for index, result in enumerate(results):
            try:
                # 打印每个结果的完整信息用于调试
                print(f"处理数据项 {index+1}/{len(results)}: {json.dumps(result, ensure_ascii=False, default=str)}")
                
                # 验证必要字段
                if not isinstance(result, dict):
                    print(f"数据项 {index+1} 不是字典格式")
                    all_items_valid = False
                    continue
                
                # 确保关键字段存在
                title = result.get('title', '无标题')
                if not title or not title.strip():
                    title = '无标题'
                
                # 尝试提取来源信息，确保标准化
                source = result.get('source', '')
                # 标准化来源名称
                if source:
                    if source.find('百度') != -1:
                        source = '百度'
                    elif source.find('B站') != -1 or source.find('Bilibili') != -1:
                        source = 'Bilibili'
                
                # 如果没有来源信息，尝试从URL推断
                if not source and 'url' in result and result['url']:
                    url = result['url']
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        print(f"解析URL: {parsed_url.netloc}")
                        if 'baidu' in parsed_url.netloc:
                            source = '百度'
                        elif 'bilibili' in parsed_url.netloc:
                            source = 'Bilibili'
                        else:
                            source = parsed_url.netloc
                    except Exception as url_e:
                        print(f"URL解析错误: {str(url_e)}")
                
                # 创建数据对象，确保所有字段都有默认值
                new_data = RawData(
                    keyword=keyword,  # 关键字是必填字段
                    title=title,
                    url=result.get('url', '') or '',
                    summary=result.get('summary', '') or '',
                    content=result.get('content', '') or result.get('summary', '') or '',
                    source=source or '未知'
                )
                
                # 验证数据模型
                try:
                    db.session.add(new_data)
                    print(f"已添加数据项 {index+1}: {title}, 来源: {source}, 关键词: {keyword}")
                    saved_count += 1
                except Exception as db_add_e:
                    print(f"添加到数据库失败，数据项 {index+1}: {str(db_add_e)}")
                    all_items_valid = False
                    continue
                
            except Exception as item_e:
                print(f"处理单个数据项 {index+1} 错误: {str(item_e)}")
                print(traceback.format_exc())
                all_items_valid = False
                continue
        
        # 只有在有数据需要保存时才提交
        if saved_count > 0:
            # 添加去重检查
            new_objects = []
            for obj in db.session.new:
                # 检查数据库中是否已存在相同的记录
                existing = RawData.query.filter_by(
                    title=obj.title,
                    url=obj.url,
                    source=obj.source
                ).first()
                
                if existing:
                    print(f"数据已存在，跳过保存: {obj.title}")
                    db.session.expunge(obj)  # 从会话中移除已存在的对象
                else:
                    new_objects.append(obj)
            
            # 更新实际要保存的数量
            actual_save_count = len(new_objects)
            
            if actual_save_count > 0:
                try:
                    # 先验证会话中的对象是否有效
                    for obj in new_objects:
                        print(f"待保存对象: {obj}")
                        # 检查关键字段
                        if not obj.keyword:
                            print(f"警告: 对象缺少关键字段keyword")
                        if not obj.title:
                            print(f"警告: 对象缺少title字段")
                        if not obj.source:
                            print(f"警告: 对象缺少source字段")
                    
                    print(f"准备提交 {actual_save_count} 条数据到数据库")
                    db.session.commit()
                    print(f"✓ 成功提交 {actual_save_count} 条数据到数据库")
                    
                    # 立即验证数据是否真正保存
                    db.session.expire_all()  # 确保我们从数据库读取最新数据
                    count_after = RawData.query.filter_by(keyword=keyword).count()
                    print(f"保存后数据库中关键词 '{keyword}' 的记录数量: {count_after}")
                    
                    if actual_save_count == saved_count:
                        return jsonify({'status': 'success', 'message': f'成功保存 {actual_save_count} 条数据到数据库'})
                    else:
                        skipped_count = saved_count - actual_save_count
                        return jsonify({'status': 'success', 'message': f'成功保存 {actual_save_count} 条数据到数据库，跳过 {skipped_count} 条重复数据'})
                except Exception as commit_e:
                    print(f"数据库提交错误: {str(commit_e)}")
                    print(traceback.format_exc())
                    return jsonify({'status': 'error', 'message': '数据库保存失败，请稍后重试'})
            else:
                print("所有数据都已存在于数据库中，无需保存")
                return jsonify({'status': 'info', 'message': '所有选中数据已存在于数据仓库中'})
        else:
            print("没有成功添加任何数据项")
            error_msg = '所有数据项处理失败，请检查数据格式'
            if not all_items_valid:
                error_msg += '，数据格式可能存在问题'
            return jsonify({'status': 'error', 'message': error_msg})
            
    except Exception as e:
        print(f"保存数据错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': '保存数据时发生系统错误，请稍后重试'})


@main.route('/data_warehouse')
@login_required
def data_warehouse():
    """
    数据仓库页面
    """
    return render_template('data_warehouse.html')


@main.route('/reports')
@login_required
def reports():
    """
    报告管理页面
    """
    return render_template('reports.html')


@main.route('/get_raw_data', methods=['GET'])
@login_required
def get_raw_data():
    """
    获取原始数据列表
    """
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        date_str = request.args.get('date', '')
        page = int(request.args.get('page', 1))
        per_page = 10
        
        print(f"获取原始数据请求 - 关键词: '{keyword}', 日期: '{date_str}', 页码: {page}")
        
        # 构建查询
        query = RawData.query
        
        # 关键词搜索 - 优化搜索范围
        if keyword:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    RawData.keyword.contains(keyword),
                    RawData.title.contains(keyword),
                    RawData.summary.contains(keyword),
                    RawData.content.contains(keyword)
                )
            )
            print(f"关键词搜索条件: {keyword}")
        
        # 日期筛选
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
                query = query.filter(
                    RawData.created_at >= target_date,
                    RawData.created_at < target_date.replace(day=target_date.day + 1)
                )
            except ValueError as e:
                print(f"日期格式错误: {str(e)}")
        
        # 分页
        pagination = query.order_by(RawData.created_at.desc()).paginate(page=page, per_page=per_page)
        
        # 格式化结果
        data = []
        for item in pagination.items:
            data.append({
                'id': item.id,
                'title': item.title,
                'url': item.url,
                'summary': item.summary,
                'content': item.content,
                'source': item.source,
                  'keyword': item.keyword,
                  'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S')
              })
        
        return jsonify({
            'status': 'success',
            'data': data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
        
    except Exception as e:
        print(f"获取数据错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': f'获取数据出错: {str(e)}'})


@main.route('/get_dates', methods=['GET'])
@login_required
def get_dates():
    """
    获取所有数据的日期列表（用于日期筛选）
    """
    try:
        # 获取所有不同的日期
        dates = db.session.query(db.func.date(RawData.created_at).label('date')).distinct().all()
        date_list = [str(date.date) for date in dates]
        
        return jsonify({'status': 'success', 'dates': sorted(date_list, reverse=True)})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取日期列表出错: {str(e)}'})


@main.route('/analyze_data', methods=['POST'])
@login_required
def analyze_data():
    """
    分析选中的原始数据，准备AI报告生成
    """
    try:
        data = request.get_json()
        raw_data_ids = data.get('raw_data_ids', [])
        
        if not raw_data_ids:
            return jsonify({'status': 'error', 'message': '请选择要分析的数据'})
            
        # 获取选中的原始数据
        selected_data = RawData.query.filter(RawData.id.in_(raw_data_ids)).all()
        
        if not selected_data:
            return jsonify({'status': 'error', 'message': '未找到选中的数据'})
            
        # 准备数据用于AI分析
        data_for_analysis = []
        for item in selected_data:
            data_for_analysis.append({
                'id': item.id,
                'title': item.title,
                'content': item.content or item.summary,
                'source': item.source,
                'url': item.url
            })
            
        # 返回数据用于前端展示或AI处理
        return jsonify({
            'status': 'success', 
            'message': '数据准备完成',
            'data': {
                'raw_data_count': len(selected_data),
                'raw_data': data_for_analysis,
                'total_word_count': sum(len(item.content or item.summary or '') for item in selected_data)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'分析数据出错: {str(e)}'})


@main.route('/save_report', methods=['POST'])
@login_required
def save_report():
    """
    保存生成的报告数据
    """
    try:
        data = request.get_json()
        title = data.get('title', '')
        content = data.get('content', '')
        related_raw_data = data.get('related_raw_data', [])
        
        if not title or not content:
            return jsonify({'status': 'error', 'message': '标题和内容不能为空'})
            
        # 创建报告数据
        report = ReportData(
            title=title,
            content=content,
            related_raw_data=','.join(map(str, related_raw_data)) if related_raw_data else None
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': '报告保存成功',
            'data': {
                'report_id': report.id,
                'title': report.title,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'保存报告出错: {str(e)}'})


@main.route('/get_reports', methods=['GET'])
@login_required
def get_reports():
    """
    获取所有报告列表
    """
    try:
        reports = ReportData.query.order_by(ReportData.created_at.desc()).all()
        
        report_list = []
        for report in reports:
            report_list.append({
                'id': report.id,
                'title': report.title,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'related_raw_data_count': len(report.related_raw_data.split(',')) if report.related_raw_data else 0
            })
            
        return jsonify({
            'status': 'success', 
            'data': {
                'reports': report_list,
                'total_count': len(reports)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取报告列表出错: {str(e)}'})


@main.route('/get_report/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """
    获取特定报告的详细信息
    """
    try:
        report = ReportData.query.get_or_404(report_id)
        
        # 获取相关的原始数据
        related_raw_data = []
        if report.related_raw_data:
            raw_data_ids = list(map(int, report.related_raw_data.split(',')))
            related_raw_data = RawData.query.filter(RawData.id.in_(raw_data_ids)).all()
            related_raw_data = [{
                'id': item.id,
                'title': item.title,
                'source': item.source,
                'url': item.url
            } for item in related_raw_data]
            
        return jsonify({
            'status': 'success', 
            'data': {
                'report': {
                    'id': report.id,
                    'title': report.title,
                    'content': report.content,
                    'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'related_raw_data': related_raw_data
                }
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取报告详情出错: {str(e)}'})


@main.route('/generate_pdf/<int:report_id>', methods=['GET'])
@login_required
def generate_pdf(report_id):
    """
    生成报告的PDF文件
    """
    try:
        report = ReportData.query.get_or_404(report_id)
        
        # 使用reportlab生成PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        # 创建PDF文档
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # 获取样式表
        styles = getSampleStyleSheet()
        
        # 定义自定义样式
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1890ff'),
            alignment=1,  # 居中对齐
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1890ff'),
            spaceBefore=12,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6,
            leading=16
        )
        
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=1,  # 居中对齐
            spaceAfter=24
        )
        
        # 构建PDF内容
        content = []
        
        # 添加标题
        content.append(Paragraph(report.title, title_style))
        
        # 添加元信息
        meta_text = f"创建时间：{report.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        content.append(Paragraph(meta_text, meta_style))
        
        # 添加报告内容标题
        content.append(Paragraph("报告内容", heading_style))
        
        # 添加报告内容（将换行符转换为<br>标签）
        report_content = report.content.replace('\n', '<br/>')
        content.append(Paragraph(report_content, body_style))
        
        # 获取相关的原始数据
        related_raw_data = []
        if report.related_raw_data:
            raw_data_ids = list(map(int, report.related_raw_data.split(',')))
            related_raw_data = RawData.query.filter(RawData.id.in_(raw_data_ids)).all()
            
        # 添加相关数据部分
        if related_raw_data:
            content.append(Spacer(1, 24))
            content.append(Paragraph("相关原始数据", heading_style))
            
            # 为每个相关数据项创建表格
            for item in related_raw_data:
                data = [
                    [Paragraph("标题", body_style), Paragraph(item.title, body_style)],
                    [Paragraph("来源", body_style), Paragraph(item.source, body_style)],
                    [Paragraph("链接", body_style), Paragraph(item.url or "", body_style)],
                    [Paragraph("摘要", body_style), Paragraph(item.summary or "", body_style)]
                ]
                
                table = Table(data, colWidths=[60, 350])
                table.setStyle(TableStyle([
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1890ff')),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f7ff'))
                ]))
                
                content.append(table)
                content.append(Spacer(1, 12))
        
        # 生成PDF
        doc.build(content)
        
        # 获取PDF内容
        buffer.seek(0)
        pdf_content = buffer.read()
        
        # 创建响应
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
        
        return response
        
    except Exception as e:
        # 记录详细错误信息
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'生成PDF出错: {str(e)}'})


@main.route('/preview_pdf/<int:report_id>', methods=['GET'])
@login_required
def preview_pdf(report_id):
    """
    预览报告的PDF文件
    """
    try:
        report = ReportData.query.get_or_404(report_id)
        
        # 使用reportlab生成PDF
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        # 创建PDF文档
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # 获取样式表
        styles = getSampleStyleSheet()
        
        # 定义自定义样式
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1890ff'),
            alignment=1,  # 居中对齐
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1890ff'),
            spaceBefore=12,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontSize=12,
            spaceBefore=6,
            spaceAfter=6,
            leading=16
        )
        
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=1,  # 居中对齐
            spaceAfter=24
        )
        
        # 构建PDF内容
        content = []
        
        # 添加标题
        content.append(Paragraph(report.title, title_style))
        
        # 添加元信息
        meta_text = f"创建时间：{report.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        content.append(Paragraph(meta_text, meta_style))
        
        # 添加报告内容标题
        content.append(Paragraph("报告内容", heading_style))
        
        # 添加报告内容（将换行符转换为<br>标签）
        report_content = report.content.replace('\n', '<br/>')
        content.append(Paragraph(report_content, body_style))
        
        # 获取相关的原始数据
        related_raw_data = []
        if report.related_raw_data:
            raw_data_ids = list(map(int, report.related_raw_data.split(',')))
            related_raw_data = RawData.query.filter(RawData.id.in_(raw_data_ids)).all()
            
        # 添加相关数据部分
        if related_raw_data:
            content.append(Spacer(1, 24))
            content.append(Paragraph("相关原始数据", heading_style))
            
            # 为每个相关数据项创建表格
            for item in related_raw_data:
                data = [
                    [Paragraph("标题", body_style), Paragraph(item.title, body_style)],
                    [Paragraph("来源", body_style), Paragraph(item.source, body_style)],
                    [Paragraph("链接", body_style), Paragraph(item.url or "", body_style)],
                    [Paragraph("摘要", body_style), Paragraph(item.summary or "", body_style)]
                ]
                
                table = Table(data, colWidths=[60, 350])
                table.setStyle(TableStyle([
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1890ff')),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f7ff'))
                ]))
                
                content.append(table)
                content.append(Spacer(1, 12))
        
        # 生成PDF
        doc.build(content)
        
        # 获取PDF内容
        buffer.seek(0)
        pdf_content = buffer.read()
        
        # 创建响应
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{report.title}.pdf"'
        
        return response
        
    except Exception as e:
        # 记录详细错误信息
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'预览PDF出错: {str(e)}'})