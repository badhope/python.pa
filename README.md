# 综合网络爬虫项目

本项目展示了多种主流Python爬虫框架的实际应用，每个框架都包含完整可运行的示例代码。

## 项目结构

```
python.pa/
├── README.md                      # 项目根说明文档
├── scrapy_example/                # Scrapy框架示例
│   ├── scrapy.cfg                 # Scrapy配置文件
│   └── spider_project/            # Scrapy项目
│       ├── spider_project/        # 项目配置模块
│       │   ├── __init__.py
│       │   ├── items.py           # 数据模型定义
│       │   ├── pipelines.py       # 数据处理管道
│       │   └── settings.py        # 配置文件
│       └── spiders/
│           └── product_spider.py  # 爬虫主程序
├── beautifulsoup_example/         # Beautiful Soup + Requests示例
│   ├── requirements.txt           # 依赖包
│   └── spider.py                  # 爬虫主程序
├── selenium_example/              # Selenium框架示例
│   ├── requirements.txt           # 依赖包
│   └── spider.py                  # 爬虫主程序
└── pyppeteer_example/             # Pyppeteer框架示例
    ├── requirements.txt           # 依赖包
    └── spider.py                  # 爬虫主程序
```

## 框架介绍

### 1. Scrapy框架
- **特点**: 企业级爬虫框架，高性能、支持异步、组件丰富
- **适用场景**: 大规模数据采集、结构化数据提取
- **优点**: 完善的爬取机制、内置请求去重、支持数据管道
- **缺点**: 学习曲线较陡、不支持JavaScript渲染

### 2. Beautiful Soup + Requests
- **特点**: 轻量级组合，简单灵活
- **适用场景**: 简单网页抓取、小规模数据采集
- **优点**: 上手简单、代码直观、调试方便
- **缺点**: 需要手动处理反爬、数据清洗工作量大

### 3. Selenium框架
- **特点**: 模拟真实浏览器、完美支持JavaScript
- **适用场景**: 动态渲染页面、复杂交互网站
- **优点**: 能抓取任何浏览器可见内容
- **缺点**: 速度慢、资源消耗大

### 4. Pyppeteer框架
- **特点**: Python版Puppeteer、无头Chrome控制
- **适用场景**: 现代Web应用爬取、SPA应用
- **优点**: 异步高效、无需浏览器GUI
- **缺点**: 配置相对复杂

## 安装依赖

```bash
# 安装所有框架依赖
pip install scrapy beautifulsoup4 requests selenium pyppeteer lxml

# Selenium需要下载对应浏览器的驱动
# 请根据需要下载ChromeDriver或GeckoDriver
```

## 使用说明

### Scrapy示例
```bash
cd scrapy_example/spider_project
scrapy crawl product_spider
```

### Beautiful Soup示例
```bash
cd beautifulsoup_example
python spider.py
```

### Selenium示例
```bash
cd selenium_example
python spider.py
```

### Pyppeteer示例
```bash
cd pyppeteer_example
python spider.py
```

## 注意事项

1. 请遵守目标网站的robots.txt规则
2. 合理设置爬取间隔，避免对服务器造成压力
3. 爬取前请确认目标网站允许爬取
4. 本项目仅供学习使用，请勿用于非法用途
