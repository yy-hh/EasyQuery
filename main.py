import os
import json
import pymysql
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ======= 配置区 =======
HOST = "your host"
PORT = 3306
USER = "user"
PASS = "pass"
DB = "db"
OUTDIR = r"E:\data"  # Windows 路径格式
CONDITIONS_DB = 'query_conditions.db'  # 用于存储查询条件的SQLite数据库
QUERY_LIMIT = 100  # 每次查询返回的最大记录数
# ======================

# 确保输出目录存在
os.makedirs(OUTDIR, exist_ok=True)
# 初始化SQLite数据库
def init_db():
    try:
        conn = sqlite3.connect(CONDITIONS_DB)
        c = conn.cursor()
        # 添加 table_name 和 field_name 字段
        c.execute('''CREATE TABLE IF NOT EXISTS queries
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      filename TEXT NOT NULL,
                      table_name TEXT NOT NULL,
                      field_name TEXT NOT NULL,
                      must_include TEXT,
                      must_exclude TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库初始化错误: {e}")
        raise
    finally:
        if conn:
            conn.close()


# 获取所有查询条件
def get_all_queries():
    queries = []
    conn = None
    try:
        conn = sqlite3.connect(CONDITIONS_DB)
        c = conn.cursor()
        c.execute("SELECT id, filename, table_name, field_name, must_include, must_exclude FROM queries ORDER BY id")
        for row in c.fetchall():
            queries.append({
                'id': row[0],
                'filename': row[1],
                'table_name': row[2],
                'field_name': row[3],
                'must_include': json.loads(row[4]) if row[4] else [],
                'must_exclude': json.loads(row[5]) if row[5] else []
            })
    except sqlite3.Error as e:
        print(f"查询获取错误: {e}")
        flash(f"数据库错误: {e}", "error")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        flash(f"数据格式错误: {e}", "error")
    finally:
        if conn:
            conn.close()
    return queries


# 添加或更新查询条件
def save_query(query_id, filename, table_name, field_name, must_include, must_exclude):
    conn = None
    try:
        conn = sqlite3.connect(CONDITIONS_DB)
        c = conn.cursor()

        # 清理输入数据
        must_include = [item.strip() for item in must_include if item.strip()]
        must_exclude = [item.strip() for item in must_exclude if item.strip()]

        # 验证必填字段
        if not filename:
            flash('文件名不能为空', 'error')
            return False

        if not table_name:
            flash('表名不能为空', 'error')
            return False

        if not field_name:
            flash('字段名不能为空', 'error')
            return False

        # 确保至少有一个条件
        if not must_include and not must_exclude:
            flash('必须提供至少一个查询条件', 'error')
            return False

        must_include_json = json.dumps(must_include)
        must_exclude_json = json.dumps(must_exclude)

        if query_id:
            # 更新现有查询
            c.execute("""UPDATE queries 
                         SET filename=?, table_name=?, field_name=?, must_include=?, must_exclude=?
                         WHERE id=?""",
                      (filename, table_name, field_name, must_include_json, must_exclude_json, query_id))
        else:
            # 添加新查询
            c.execute("""INSERT INTO queries 
                         (filename, table_name, field_name, must_include, must_exclude) 
                         VALUES (?, ?, ?, ?, ?)""",
                      (filename, table_name, field_name, must_include_json, must_exclude_json))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"保存查询错误: {e}")
        flash(f"数据库保存错误: {e}", "error")
        return False
    except Exception as e:
        print(f"保存查询时发生意外错误: {e}")
        flash(f"保存失败: {e}", "error")
        return False
    finally:
        if conn:
            conn.close()


# 删除查询条件
def delete_query(query_id):
    conn = None
    try:
        conn = sqlite3.connect(CONDITIONS_DB)
        c = conn.cursor()
        c.execute("DELETE FROM queries WHERE id=?", (query_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"删除查询错误: {e}")
        flash(f"数据库删除错误: {e}", "error")
        return False
    finally:
        if conn:
            conn.close()


# SQL构建器函数 - 支持自定义表和字段
def build_query(conditions):
    try:
        table_name = conditions.get('table_name', 'report_struct_diag_data')
        field_name = conditions.get('field_name', 'diag_data')

        # 基本SQL结构
        base_sql = f"SELECT id, {field_name} FROM {table_name}"

        where_clauses = []

        # 处理必须包含的条件
        if conditions.get('must_include'):
            for pattern in conditions['must_include']:
                # 安全处理 - 转义特殊字符
                safe_pattern = pattern.replace("'", "''")
                where_clauses.append(f"{field_name} LIKE '%{safe_pattern}%'")

        # 处理必须排除的条件
        if conditions.get('must_exclude'):
            for pattern in conditions['must_exclude']:
                # 安全处理 - 转义特殊字符
                safe_pattern = pattern.replace("'", "''")
                where_clauses.append(f"{field_name} NOT LIKE '%{safe_pattern}%'")

        # 组合WHERE子句
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            base_sql += f" WHERE {where_sql}"

        # 添加排序和限制
        base_sql += f" ORDER BY id DESC LIMIT {QUERY_LIMIT}"

        return base_sql
    except Exception as e:
        print(f"SQL构建错误: {e}")
        return None


def export_query_to_json(connection, sql, filename):
    if not sql:
        print("SQL语句为空，跳过执行")
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            # 将结果转换为字典列表
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]

        filepath = os.path.join(OUTDIR, filename + ".json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath
    except pymysql.Error as e:
        print(f"数据库查询错误: {e}")
        return None
    except Exception as e:
        print(f"导出JSON错误: {e}")
        return None


# Flask路由
@app.route('/')
def index():
    try:
        queries = get_all_queries()
        return render_template('index.html', queries=queries)
    except Exception as e:
        flash(f"加载页面错误: {e}", "error")
        return render_template('index.html', queries=[])


@app.route('/add', methods=['GET', 'POST'])
def add_query():
    if request.method == 'POST':
        filename = request.form.get('filename', '').strip()
        table_name = request.form.get('table_name', '').strip()
        field_name = request.form.get('field_name', '').strip()
        must_include = request.form.getlist('must_include[]')
        must_exclude = request.form.getlist('must_exclude[]')

        if save_query(None, filename, table_name, field_name, must_include, must_exclude):
            flash('查询条件已保存', 'success')
            return redirect(url_for('index'))
        else:
            return render_template('edit.html',
                                   filename=filename,
                                   table_name=table_name,
                                   field_name=field_name,
                                   must_include=must_include,
                                   must_exclude=must_exclude)

    return render_template('edit.html')


@app.route('/edit/<int:query_id>', methods=['GET', 'POST'])
def edit_query(query_id):
    try:
        queries = get_all_queries()
        query = next((q for q in queries if q['id'] == query_id), None)

        if not query:
            flash('查询条件不存在', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            filename = request.form.get('filename', '').strip()
            table_name = request.form.get('table_name', '').strip()
            field_name = request.form.get('field_name', '').strip()
            must_include = request.form.getlist('must_include[]')
            must_exclude = request.form.getlist('must_exclude[]')

            if save_query(query_id, filename, table_name, field_name, must_include, must_exclude):
                flash('查询条件已更新', 'success')
                return redirect(url_for('index'))
            else:
                return render_template('edit.html',
                                       query=query,
                                       filename=filename,
                                       table_name=table_name,
                                       field_name=field_name,
                                       must_include=must_include,
                                       must_exclude=must_exclude)

        return render_template('edit.html', query=query)
    except Exception as e:
        flash(f"编辑错误: {e}", "error")
        return redirect(url_for('index'))


@app.route('/delete/<int:query_id>')
def delete_query_route(query_id):
    if delete_query(query_id):
        flash('查询条件已删除', 'success')
    else:
        flash('删除查询条件失败', 'error')
    return redirect(url_for('index'))


@app.route('/run')
def run_queries():
    try:
        queries = get_all_queries()
        if not queries:
            flash('没有可执行的查询条件', 'warning')
            return redirect(url_for('index'))

        conn = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASS,
            db=DB,
            charset='utf8mb4',
            connect_timeout=10
        )

        results = []
        success_count = 0

        for query in queries:
            sql = build_query(query)
            if not sql:
                results.append({
                    'filename': query['filename'],
                    'filepath': 'SQL生成失败',
                    'sql': '无效的SQL语句',
                    'error': True
                })
                continue

            filepath = export_query_to_json(conn, sql, query['filename'])
            if filepath:
                results.append({
                    'filename': query['filename'],
                    'filepath': filepath,
                    'sql': sql,
                    'error': False
                })
                success_count += 1
            else:
                results.append({
                    'filename': query['filename'],
                    'filepath': '导出失败',
                    'sql': sql,
                    'error': True
                })

        conn.close()

        if success_count == 0:
            flash('所有查询执行失败', 'error')
        elif success_count < len(queries):
            flash(f'部分查询执行成功 ({success_count}/{len(queries)})', 'warning')
        else:
            flash(f'所有查询执行成功 ({len(queries)}个)', 'success')

        return render_template('results.html', results=results)
    except pymysql.Error as e:
        flash(f'数据库连接失败: {e}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'执行查询时发生错误: {e}', 'error')
        return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', error=str(e)), 500


if __name__ == '__main__':
    init_db()
    try:
        # 获取本机IP地址
        import socket

        host_name = socket.gethostname()
        ip_address = socket.gethostbyname(host_name)
        print(f"本机IP地址: {ip_address}")
        print(f"局域网访问地址: http://{ip_address}:5001")
    except Exception as e:
        print(f"无法获取本机IP地址: {e}")
        print("请手动检查本机IP地址")

    # 允许局域网访问
    app.run(debug=True, host='0.0.0.0', port=5001)