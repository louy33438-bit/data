#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili搜索爬虫程序
功能：根据用户输入的关键词，爬取Bilibili搜索结果的数据
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random

class BilibiliSpider:
    def __init__(self):
        # 使用用户提供的请求头信息
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'search.bilibili.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SLBrowser/9.0.6.8151 SLBChan/112 SLBVPV/64-bit',
            'Sec-Ch-Ua': '"Chromium";v="9", "Not?A_Brand";v="8"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
        # 添加用户提供的cookies
        self.cookies = {
            'buvid3': 'FF4EE0ED-1F47-2EC7-BF63-B3E542DB113E92248infoc',
            'b_nut': '1733567392',
            '_uuid': 'F6699B25-3289-58A7-4447-4C1FB61023FCB93812infoc',
            'buvid_fp': '0aa080af2d42e7a04cc5e34d5ffb4615',
            'rpdid': '0z9ZwfQkDO|tYy10FNK|SFj|3w1TjS4s',
            'header_theme_version': 'CLOSE',
            'enable_web_push': 'DISABLE',
            'b_lsid': '579CFCD10_19AD3B573EA',
            'bsource': 'search_baidu',
            'home_feed_column': '5',
            'browser_resolution': '1659-915',
            'bmg_af_switch': '1',
            'bmg_src_def_domain': 'i2.hdslb.com',
            'CURRENT_FNVAL': '2000',
            'sid': 'qlmnxp4w'
        }
    
    def search(self, keyword, page=1):
        """
        执行Bilibili搜索
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            搜索结果列表
        """
        try:
            # URL编码关键词
            encoded_keyword = urllib.parse.quote(keyword)
            
            # 构造搜索URL
            # Bilibili搜索结果通常使用pn参数表示页码，每页10条结果
            pn = (page - 1) * 10
            url = f'https://search.bilibili.com/all?keyword={encoded_keyword}&pn={pn}&from_source=webtop_search&spm_id_from=333.1007&search_source=3'
            
            print(f'正在搜索Bilibili关键词: {keyword}, 页码: {page}')
            print(f'请求URL: {url}')
            
            # 添加随机延迟，模拟人类行为
            time.sleep(random.uniform(2, 4))
            
            # 创建会话
            session = requests.Session()
            
            # 随机修改一些请求头信息
            headers = self.headers.copy()
            # 随机选择不同的User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 SLBrowser/9.0.6.8151 SLBChan/112 SLBVPV/64-bit',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/125.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0'
            ]
            headers['User-Agent'] = random.choice(user_agents)
            
            # 设置请求头和cookies
            session.headers.update(headers)
            if self.cookies:
                session.cookies.update(self.cookies)
            
            # 先访问Bilibili首页建立会话
            home_response = session.get('https://www.bilibili.com/', timeout=5)
            print(f'首页请求状态码: {home_response.status_code}')
            
            # 再次添加延迟
            time.sleep(random.uniform(1, 2))
            
            # 添加referer头
            session.headers.update({'Referer': 'https://www.bilibili.com/'})
            
            # 发送搜索请求
            response = session.get(url, timeout=10)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            # 调试信息
            print(f'搜索请求状态码: {response.status_code}')
            print(f'响应内容长度: {len(response.text)} 字符')
            
            # 检查是否有验证信息
            if '验证码' in response.text or '安全验证' in response.text:
                print('警告: 可能被Bilibili识别为爬虫，需要验证码验证')
                with open('bilibili_captcha_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print('验证页面已保存到 bilibili_captcha_page.html')
            
            # 解析响应内容
            results = self._parse_response(response.text)
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f'请求出错: {e}')
            try:
                with open('bilibili_error_page.html', 'w', encoding='utf-8') as f:
                    f.write(str(e))
                print('错误页面已保存到 bilibili_error_page.html')
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
            with open('bilibili_debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print('调试页面已保存到 bilibili_debug_page.html')
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 检查页面是否包含搜索结果的特征
            if 'search-list' in html_content or 'video-list' in html_content:
                print('检测到搜索结果页面特征')
            else:
                print('未检测到搜索结果页面特征，可能被反爬')
            
            # 尝试提取视频搜索结果
            # 查找视频卡片元素
            video_items = []
            
            # 尝试多种可能的选择器
            selectors = [
                '.video-list-item',  # 常见的视频列表项类名
                '.video-card',      # 视频卡片类名
                '.search-item',     # 搜索项类名
                '.list-item',       # 列表项类名
                'li[data-id]'       # 可能带有数据ID的列表项
            ]
            
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    video_items.extend(items)
                    print(f'通过选择器 {selector} 找到 {len(items)} 个视频项')
            
            # 如果直接选择器没有找到，尝试查找包含href的链接
            if not video_items:
                print('尝试使用链接查找方法')
                all_a_tags = soup.find_all('a', href=True)
                # 过滤出可能的视频链接（通常包含/video/或BV号）
                video_links = []
                for a in all_a_tags:
                    href = a['href']
                    if ('/video/' in href or 'BV' in href.upper()) and len(href) > 20:
                        parent = a.find_parent()
                        if parent and parent not in video_links:
                            video_links.append(parent)
                video_items = video_links
                print(f'找到 {len(video_items)} 个可能的视频链接')
            
            # 解析找到的视频项
            for item in video_items:
                try:
                    result = {}
                    
                    # 提取标题
                    title_elem = item.find(['h3', 'h2', 'a'], class_=lambda x: x and ('title' in x or 'name' in x))
                    if not title_elem:
                        # 尝试查找所有可能包含标题的a标签
                        a_tags = item.find_all('a', href=True)
                        for a in a_tags:
                            if len(a.get_text(strip=True)) > 5 and ('/video/' in a['href'] or 'BV' in a['href'].upper()):
                                title_elem = a
                                break
                    
                    if title_elem:
                        result['title'] = title_elem.get_text(strip=True)
                        # 获取链接
                        if title_elem.get('href'):
                            href = title_elem['href']
                            if not href.startswith('http'):
                                href = 'https:' + href if href.startswith('//') else 'https://www.bilibili.com' + href
                            result['url'] = href
                    
                    # 提取播放量、弹幕数等信息
                    stats = item.find_all(['span', 'div'], class_=lambda x: x and ('play' in x or 'view' in x or 'danmaku' in x or 'stat' in x))
                    stats_text = ' '.join([s.get_text(strip=True) for s in stats])
                    if stats_text:
                        result['stats'] = stats_text
                    
                    # 提取UP主信息
                    up_elem = item.find(['span', 'div'], class_=lambda x: x and ('up' in x or 'author' in x))
                    if up_elem:
                        result['author'] = up_elem.get_text(strip=True)
                    
                    # 提取视频简介
                    desc_elem = item.find(['p', 'div'], class_=lambda x: x and ('desc' in x or 'description' in x or 'intro' in x))
                    if desc_elem:
                        result['summary'] = desc_elem.get_text(strip=True)
                    
                    # 如果没有简介，尝试从其他文本元素提取
                    if 'summary' not in result:
                        text_elems = item.find_all(['p', 'div', 'span'])
                        for elem in text_elems:
                            text = elem.get_text(strip=True)
                            if len(text) > 20 and len(text) < 200 and 'summary' not in result:
                                result['summary'] = text
                    
                    # 只添加有效结果
                    if 'title' in result and len(result['title']) > 5:
                        results.append(result)
                        print(f'添加结果: {result["title"]}')
                        # 最多返回10个结果
                        if len(results) >= 10:
                            break
                except Exception as e:
                    print(f'解析单个视频项出错: {e}')
            
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
            filename = f'Bilibili搜索结果_{keyword}_{time.strftime("%Y%m%d_%H%M%S")}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f'Bilibili搜索结果 - 关键词: {keyword}\n')
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
                    if 'author' in result:
                        f.write(f'UP主: {result["author"]}\n')
                    if 'stats' in result:
                        f.write(f'数据: {result["stats"]}\n')
                    if 'type' in result and result['type'] == 'text':
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
    print("欢迎使用Bilibili搜索爬虫")
    print("本程序可以根据关键词爬取Bilibili搜索结果")
    print("=" * 60)
    
    # 创建爬虫实例
    spider = BilibiliSpider()
    
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
                if 'author' in result:
                    print(f'UP主: {result["author"]}')
                if 'stats' in result:
                    print(f'数据: {result["stats"]}')
            
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
                if 'author' in result:
                    print(f'UP主: {result["author"]}')
                if 'stats' in result:
                    print(f'数据: {result["stats"]}')
            
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
    模块级别的搜索函数，直接执行Bilibili搜索
    
    Args:
        keyword: 搜索关键词
        page: 页码
        
    Returns:
        搜索结果列表
    """
    try:
        spider = BilibiliSpider()
        return spider.search(keyword, page)
    except Exception as e:
        print(f"模块级搜索函数出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return []