# 百度搜索爬虫

这是一个基于Python的百度搜索爬虫程序，可以根据用户输入的关键词动态爬取百度搜索结果。

## 功能特性

- ✅ 支持动态关键词搜索
- ✅ 支持多页结果爬取
- ✅ 提取搜索结果的标题、链接、摘要和来源
- ✅ 结果保存为文本文件
- ✅ 模拟浏览器请求头，降低被反爬风险
- ✅ 添加随机延迟，避免频繁请求

## 技术栈

- Python 3.x
- requests - 发送HTTP请求
- beautifulsoup4 - 解析HTML内容
- lxml - HTML解析器

## 快速开始

### 1. 克隆或下载项目

```bash
git clone https://your-repository-url/baidu-spider.git
cd baidu-spider
```

### 2. 创建并激活虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行爬虫

```bash
python baidu_spider.py
```

### 5. 使用说明

- 运行后，输入搜索关键词
- 输入要爬取的页数（默认为1页）
- 程序会显示结果预览
- 可以选择保存结果到文件
- 输入'退出'结束程序

## 注意事项

1. **合法使用**：请遵守相关法律法规和网站的robots协议，不要用于恶意爬取
2. **频率控制**：程序已添加随机延迟，但仍请合理控制爬取频率
3. **IP限制**：如果频繁爬取可能会触发百度的反爬机制，导致IP被临时限制
4. **自定义配置**：可以在代码中修改请求头和cookies以提高成功率
5. **结果解析**：由于百度搜索结果页面结构可能变化，解析部分可能需要根据实际情况调整

## 项目结构

```
baidu-spider/
├── baidu_spider.py  # 主程序文件
├── requirements.txt # 依赖包列表
├── README.md        # 使用说明
└── venv/            # Python虚拟环境（不包含在版本控制中）
```

## 常见问题

### Q: 运行时提示连接超时
A: 可能是网络问题或百度限制了访问，请检查网络连接或稍后再试

### Q: 没有提取到搜索结果
A: 百度可能更新了页面结构，需要调整解析规则

### Q: 如何提高爬虫的稳定性
A: 可以尝试添加代理IP、使用更完善的cookies、进一步降低爬取频率

## 更新日志

- v1.0.0: 初始版本，实现基本搜索和结果提取功能

## License

MIT