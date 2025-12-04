#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索爬虫程序
功能：根据用户输入的关键词，爬取百度搜索结果的文本数据
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

class BaiduSpider:
    def __init__(self):
        # 使用更真实的浏览器请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'www.baidu.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 添加一些基础cookies以模拟正常访问
        self.cookies = {
            'BDORZ': 'FFFB88E999055A3F8A630C64834BD6D0',
            'BAIDUID': '154B547D9085A05D2B4F5500D935A2EF:FG=1'
        }
    
    def search(self, keyword, page=1):
        """
        执行百度搜索
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            搜索结果列表
        """
        try:
            # URL编码关键词
            encoded_keyword = urllib.parse.quote(keyword)
            
            # 构造更完整的搜索URL，包含更多参数
            start = (page - 1) * 10
            # 添加一些常见的URL参数以模拟真实搜索
            url = f'https://www.baidu.com/s?wd={encoded_keyword}&pn={start}&oq={encoded_keyword}&ie=utf-8&rsv_idx=2&rsv_pq=b0c73e8902c9f41c&rsv_t=5d7aS8LbX3XJ7X6zX5zX4zX3zX2zX1zX0'
            
            print(f'正在搜索关键词: {keyword}, 页码: {page}')
            print(f'请求URL: {url}')
            
            # 添加较长的随机延迟，更接近人类行为
            time.sleep(random.uniform(2, 4))
            
            # 创建会话
            session = requests.Session()
            
            # 随机修改一些请求头信息，避免被识别为爬虫
            headers = self.headers.copy()
            # 随机选择不同的User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/88.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
            ]
            headers['User-Agent'] = random.choice(user_agents)
            
            session.headers.update(headers)
            if self.cookies:
                session.cookies.update(self.cookies)
            
            # 先发送一个请求到百度首页，获取Cookie和建立会话
            home_response = session.get('https://www.baidu.com/', timeout=5)
            print(f'首页请求状态码: {home_response.status_code}')
            
            # 再次添加延迟
            time.sleep(random.uniform(1, 2))
            
            # 添加referer头
            session.headers.update({'Referer': 'https://www.baidu.com/'})
            
            # 发送搜索请求
            response = session.get(url, timeout=10)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            # 调试信息
            print(f'搜索请求状态码: {response.status_code}')
            print(f'响应内容长度: {len(response.text)} 字符')
            
            # 检查是否被百度识别为爬虫
            if '百度安全验证' in response.text or '请输入验证码' in response.text:
                print('警告: 可能被百度识别为爬虫，需要验证码验证')
                with open('captcha_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print('验证页面已保存到 captcha_page.html')
            
            # 解析响应内容
            results = self._parse_response(response.text)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f'请求出错: {e}')
            try:
                with open('error_page.html', 'w', encoding='utf-8') as f:
                    f.write(str(e))
                print('错误页面已保存到 error_page.html')
            except:
                pass
            return []
        except Exception as e:
            print(f'搜索过程出错: {e}')
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_response(self, html_content):
        """
        解析HTML响应内容，提取搜索结果
        
        Args:
            html_content: HTML内容
            
        Returns:
            解析后的结果列表
        """
        results = []
        
        try:
            # 保存完整的HTML以便调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('调试页面已保存到 debug_page.html')
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')  # 使用更简单的解析器
            
            # 检查页面是否包含搜索结果的特征文本
            if '百度为您找到相关结果约' in html_content:
                print('检测到搜索结果页面特征')
            else:
                print('未检测到搜索结果页面特征，可能被反爬')
            
            # 尝试使用更简单直接的方法查找结果
            # 1. 查找所有包含href属性的a标签
            all_a_tags = soup.find_all('a', href=True)
            print(f'找到 {len(all_a_tags)} 个链接标签')
            
            # 过滤出可能的搜索结果链接
            candidate_links = []
            for a in all_a_tags:
                href = a['href']
                text = a.get_text(strip=True)
                
                # 过滤条件：
                # - 链接长度适中
                # - 文本长度适中
                # - 不是JavaScript链接
                # - 可能包含/link?url= 或 http
                if (len(href) > 20 and 
                    len(text) > 5 and len(text) < 200 and 
                    not href.startswith('javascript:') and 
                    (href.startswith('/link?url=') or href.startswith('http'))):
                    
                    # 查找这个链接的父元素，尝试获取摘要
                    summary = ''
                    parent = a.find_parent()
                    if parent:
                        # 查找可能包含摘要的相邻元素
                        for sibling in parent.find_next_siblings():
                            sib_text = sibling.get_text(strip=True)
                            if len(sib_text) > 20 and len(sib_text) < 300:
                                summary = sib_text
                                break
                    
                    candidate_links.append({
                        'title': text,
                        'url': href if href.startswith('http') else 'https://www.baidu.com' + href,
                        'summary': summary
                    })
            
            print(f'过滤后得到 {len(candidate_links)} 个候选链接')
            
            # 去重处理
            seen_titles = set()
            for link in candidate_links:
                if link['title'] not in seen_titles and len(link['title']) > 8:
                    seen_titles.add(link['title'])
                    results.append(link)
                    print(f'添加结果: {link["title"]}')
                    # 最多返回10个结果
                    if len(results) >= 10:
                        break
            
            # 如果仍然没有找到结果，尝试提取页面中的文本内容
            if not results:
                print('尝试提取页面中的文本内容...')
                # 提取所有段落和div文本
                all_texts = []
                for tag in soup.find_all(['p', 'div', 'span']):
                    text = tag.get_text(strip=True)
                    if len(text) > 50 and len(text) < 500:
                        all_texts.append(text)
                
                # 添加前3个较长的文本片段
                for i, text in enumerate(all_texts[:3]):
                    results.append({
                        'type': 'text',
                        'content': text[:200] + '...'
                    })
            
            print(f'最终解析到 {len(results)} 条有效结果')
            
        except Exception as e:
            print(f'解析HTML出错: {e}')
            import traceback
            traceback.print_exc()
        
        return results
    
    def save_results(self, results, keyword):
        """
        保存搜索结果到文件
        
        Args:
            results: 搜索结果列表
            keyword: 搜索关键词
        """
        try:
            filename = f'搜索结果_{keyword}_{time.strftime("%Y%m%d_%H%M%S")}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'百度搜索结果 - 关键词: {keyword}\n')
                f.write(f'时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'找到 {len(results)} 条结果\n')
                f.write('=' * 80 + '\n\n')
                
                for i, result in enumerate(results, 1):
                    f.write(f'结果 {i}:\n')
                    if 'title' in result:
                        f.write(f'标题: {result["title"]}\n')
                    if 'url' in result:
                        f.write(f'链接: {result["url"]}\n')
                    if 'summary' in result:
                        f.write(f'摘要: {result["summary"]}\n')
                    if 'source' in result:
                        f.write(f'来源: {result["source"]}\n')
                    if 'type' in result and result['type'] == 'special':
                        f.write(f'内容: {result["content"]}\n')
                    f.write('-' * 80 + '\n\n')
            
            print(f'结果已保存到: {filename}')
            return filename
            
        except Exception as e:
            print(f'保存结果出错: {e}')
            return None

def main():
    """
    主函数，处理用户输入和执行搜索
    """
    import sys
    
    print("=" * 60)
    print("欢迎使用百度搜索爬虫")
    print("本程序可以根据关键词爬取百度搜索结果")
    print("=" * 60)
    
    # 创建爬虫实例
    spider = BaiduSpider()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 从命令行获取关键词
        keyword = sys.argv[1]
        
        # 从命令行获取页数（可选）
        page_count = 1
        if len(sys.argv) > 2:
            try:
                page_count = int(sys.argv[2])
                if page_count < 1:
                    page_count = 1
            except ValueError:
                print("无效的页数参数，将爬取1页")
                page_count = 1
        
        print(f"\n从命令行获取关键词: {keyword}")
        print(f"要爬取的页数: {page_count}")
        
        # 执行搜索
        all_results = []
        for page in range(1, page_count + 1):
            results = spider.search(keyword, page)
            all_results.extend(results)
            
            # 如果不是最后一页，添加延迟
            if page < page_count:
                time.sleep(random.uniform(2, 5))
        
        # 显示结果
        print(f'\n共找到 {len(all_results)} 条结果\n')
        
        if all_results:
            # 打印前5条结果作为预览
            print("前几条结果预览:")
            for i, result in enumerate(all_results[:5], 1):
                print(f'\n结果 {i}:')
                if 'title' in result:
                    print(f'标题: {result["title"]}')
                if 'url' in result:
                    print(f'链接: {result["url"]}')
                if 'summary' in result:
                    print(f'摘要: {result["summary"]}')
                if 'source' in result:
                    print(f'来源: {result["source"]}')
                if 'type' in result and result['type'] == 'special':
                    print(f'内容: {result["content"]}')
            
            # 自动保存结果
            print("\n正在保存结果到文件...")
            spider.save_results(all_results, keyword)
        else:
            print("没有找到相关结果")
        
        print("\n搜索完成！")
        return
    
    # 如果没有命令行参数，进入交互模式
    while True:
        # 获取用户输入
        keyword = input("\n请输入搜索关键词（输入'退出'结束程序）: ")
        
        if keyword.lower() in ['退出', 'exit', 'quit', 'q']:
            print("感谢使用，再见！")
            break
        
        if not keyword.strip():
            print("关键词不能为空，请重新输入")
            continue
        
        try:
            page_count = input("请输入要爬取的页数（默认1页）: ")
            page_count = int(page_count) if page_count.strip() else 1
            if page_count < 1:
                page_count = 1
        except ValueError:
            print("无效的页数，将爬取1页")
            page_count = 1
        
        # 执行搜索
        all_results = []
        for page in range(1, page_count + 1):
            results = spider.search(keyword, page)
            all_results.extend(results)
            
            # 如果不是最后一页，添加延迟
            if page < page_count:
                time.sleep(random.uniform(2, 5))
        
        # 显示结果
        print(f'\n共找到 {len(all_results)} 条结果\n')
        
        if all_results:
            # 打印前5条结果作为预览
            print("前几条结果预览:")
            for i, result in enumerate(all_results[:5], 1):
                print(f'\n结果 {i}:')
                if 'title' in result:
                    print(f'标题: {result["title"]}')
                if 'url' in result:
                    print(f'链接: {result["url"]}')
                if 'summary' in result:
                    print(f'摘要: {result["summary"]}')
                if 'source' in result:
                    print(f'来源: {result["source"]}')
                if 'type' in result and result['type'] == 'special':
                    print(f'内容: {result["content"]}')
            
            # 保存结果
            save_choice = input("\n是否保存所有结果到文件？(y/n): ")
            if save_choice.lower() in ['y', 'yes']:
                spider.save_results(all_results, keyword)
        else:
            print("没有找到相关结果")

if __name__ == '__main__':
    main()

# 模块级别的search函数，方便其他模块直接调用
def search(keyword, page=1):
    """
    模块级别的搜索函数，直接执行百度搜索
    
    Args:
        keyword: 搜索关键词
        page: 页码
        
    Returns:
        搜索结果列表
    """
    try:
        spider = BaiduSpider()
        return spider.search(keyword, page)
    except Exception as e:
        print(f"模块级搜索函数出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return []