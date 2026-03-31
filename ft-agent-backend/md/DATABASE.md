# 数据库配置快速指南

## 数据库切换说明

本系统支持两种数据库：

| 数据库 | 适用场景 | 配置方式 |
|--------|---------|---------|
| **SQLite** | 开发环境、单用户测试 | `DB_TYPE=sqlite` |
| **PostgreSQL** | 生产环境、多用户部署 | `DB_TYPE=postgresql` |

---

## 开发环境配置（默认）

使用 SQLite，无需额外配置：

```env
# .env 文件
DB_TYPE=sqlite
```

启动即可：
```bash
python main.py
```

---

## 生产环境配置

### 方法 1: 本地 PostgreSQL

1. **安装 PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. **创建数据库**
```bash
sudo -u postgres psql
```

在 PostgreSQL 命令行中：
```sql
CREATE DATABASE agent_db;
CREATE USER agent_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;
\q
```

3. **配置 .env**
```env
DB_TYPE=postgresql
DB_USER=agent_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agent_db
```

4. **安装 Python 驱动**
```bash
pip install psycopg2-binary
```

5. **启动服务**
```bash
python main.py
```

### 方法 2: 云数据库（推荐）

#### 阿里云 RDS
1. 创建 PostgreSQL 实例
2. 获取连接信息
3. 配置白名单
4. 更新 .env

```env
DB_TYPE=postgresql
DB_USER=your_rds_user
DB_PASSWORD=your_rds_password
DB_HOST=rm-xxxxx.pg.rds.aliyuncs.com
DB_PORT=5432
DB_NAME=agent_db
```

#### 腾讯云 TencentDB
类似步骤，从控制台获取连接信息。

---

## 数据迁移

从 SQLite 迁移到 PostgreSQL：

```bash
# 1. 配置 PostgreSQL 连接（在 .env 中）
# 2. 运行迁移脚本
python migrate_db.py
```

迁移完成后：
```bash
# 修改 .env
DB_TYPE=postgresql

# 重启服务
python main.py
```

---

## 验证配置

启动服务时会显示当前使用的数据库：

```bash
python main.py

# 输出示例：
# ✓ 使用 PostgreSQL 数据库: localhost:5432/agent_db
# ✓ 数据库表初始化完成
```

---

## 常见问题

### Q1: 如何查看当前使用的数据库？
**A:** 启动服务时会在控制台打印数据库信息。

### Q2: 可以在开发和生产环境使用不同的数据库吗？
**A:** 可以！通过不同的 .env 文件配置：
- 开发环境：`.env` → `DB_TYPE=sqlite`
- 生产环境：`.env.production` → `DB_TYPE=postgresql`

### Q3: PostgreSQL 连接失败怎么办？
**A:** 检查：
1. 数据库服务是否运行
2. 连接信息是否正确
3. 防火墙/安全组是否允许连接
4. 用户权限是否正确

### Q4: 如何备份数据？
**A:**
- **SQLite**: 复制 `sql_app.db` 文件
- **PostgreSQL**: 使用 `pg_dump`
  ```bash
  pg_dump -U agent_user -h localhost agent_db > backup.sql
  ```

### Q5: 生产环境必须用 PostgreSQL 吗？
**A:** 强烈推荐！理由：
- ✅ 支持多用户并发
- ✅ 数据安全性高
- ✅ 性能更好
- ✅ 支持横向扩展

---

## 性能对比

| 指标 | SQLite | PostgreSQL |
|------|--------|-----------|
| 并发写入 | 单线程 | 多线程 |
| 最大连接数 | ~100 | 100-1000+ |
| 数据安全 | 中等 | 高 |
| 备份恢复 | 简单 | 完善 |
| 生产就绪 | ❌ | ✅ |

---

## 推荐配置

### 小型项目（<100 用户）
- **开发**: SQLite
- **生产**: PostgreSQL（单实例）

### 中型项目（100-10000 用户）
- **开发**: SQLite
- **生产**: PostgreSQL（主从复制）

### 大型项目（>10000 用户）
- **开发**: SQLite
- **生产**: PostgreSQL（集群 + 读写分离）

---

## 更多信息

- 详细部署指南：查看 [DEPLOYMENT.md](./DEPLOYMENT.md)
- 数据库优化：查看 DEPLOYMENT.md 中的性能优化章节
