# EasyQuery

一个基于 Flask 的简单查询工具，用于管理和执行数据库查询条件，并将结果导出为 JSON 文件。

## 功能特点

- 支持添加、编辑和删除查询条件
- 可自定义表名和字段名
- 支持必须包含和必须排除的查询条件
- 查询结果自动导出为 JSON 格式
- 支持批量执行多个查询条件
- Web 界面操作，支持局域网访问

## 安装步骤

1. 克隆项目到本地：
```bash
git clone [你的仓库地址]
cd EasyQuery
pip install -r requirements.txt

## 配置说明
在 main.py 中可以修改以下配置项：

- 数据库连接信息（HOST, PORT, USER, PASS, DB）
- 输出目录（OUTDIR）
- 查询条件数据库文件名（CONDITIONS_DB）
- 查询结果限制数（QUERY_LIMIT
```bash
python main.py
在浏览器中访问：
本地访问：http://localhost:5001
局域网访问：http://[本机IP]:5001
主要功能
添加查询条件

设置输出文件名
指定数据库表名
指定查询字段
添加必须包含的条件
添加必须排除的条件
管理查询条件

查看所有查询条件
编辑现有条件
删除查询条件
执行查询

批量执行所有查询条件
自动导出 JSON 结果
查看执行状态和结果
注意事项
确保配置的输出目录具有写入权限
建议定期备份查询条件数据库
大量数据查询时注意 QUERY_LIMIT 的设置
技术栈
Python 3.x
Flask
SQLite3（存储查询条件）
PyMySQL（连接 MySQL 数据库）
EasyQuery/
├── main.py              # 主程序文件
├── requirements.txt     # 项目依赖
├── templates/           # HTML 模板
│   ├── index.html      # 主页面
│   ├── edit.html       # 编辑页面
│   ├── results.html    # 结果页面
│   ├── 404.html        # 404错误页面
│   └── 500.html        # 500错误页面
└── README.md           # 项目说明文档
## 开发计划
- 添加用户认证功能
- 支持更多数据库类型
- 添加查询结果预览功能
- 支持导出更多文件格式
- 添加查询条件模板功能
- 优化查询性能