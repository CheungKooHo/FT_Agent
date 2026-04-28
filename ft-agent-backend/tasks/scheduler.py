"""
定时任务调度器
用于定时抓取财税政策并入库到知识库
"""
import asyncio
import re
import uuid
import httpx
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# 定时任务实例
scheduler = BlockingScheduler()

# 政策来源配置
POLICY_SOURCES = [
    {
        "name": "国家税务总局",
        "base_url": "https://www.chinatax.gov.cn/clients/newtax/index.html",
        "list_pattern": r'href="(/clients/[^"]*\.html[^"]*)"[^>]*>([^<]+)</a>',
    }
]


def parse_policy_list(html: str, base_url: str) -> list:
    """从列表页提取政策链接"""
    links = []
    # 匹配政策详情页链接
    pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
    for match in re.finditer(pattern, html):
        href = match.group(1)
        title = match.group(2).strip()
        # 过滤有效链接
        if '/claws/' in href or '/newtax/' in href:
            if not href.startswith('http'):
                href = base_url.replace('/clients/newtax/index.html', '') + href
            links.append({"url": href, "title": title})
    return links[:10]  # 最多取10条


async def fetch_policy_detail(url: str, client: httpx.AsyncClient) -> dict:
    """抓取单个政策详情页"""
    try:
        response = await client.get(url, timeout=30.0)
        if response.status_code == 200:
            html = response.text

            # 提取标题
            title_match = re.search(r'<title>([^<]+)</title>', html)
            title = title_match.group(1).strip() if title_match else url

            # 提取发布日期
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html)
            pub_date = None
            if date_match:
                pub_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}"

            # 提取正文内容（移除script和style）
            content = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', '\n', content).strip()

            # 去除太短的行
            lines = [line.strip() for line in content.split('\n') if len(line.strip()) > 20]
            main_content = '\n'.join(lines)

            return {
                "title": title,
                "url": url,
                "content": main_content[:8000],  # 限制长度
                "pub_date": pub_date,
                "source": "国家税务总局"
            }
    except Exception as e:
        print(f"    抓取失败: {url} - {e}")
    return None


async def save_to_knowledge_base(policy: dict, db) -> bool:
    """保存政策到知识库"""
    from core.database import KnowledgeFile
    from core.rag_engine import upload_and_index_pdf, delete_from_vectorstore

    try:
        # 生成唯一ID
        doc_id = str(uuid.uuid4())[:8]
        safe_title = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', policy['title'])[:50]
        filename = f"{safe_title}_{doc_id}.txt"
        filepath = Path(f"./uploads/{filename}")

        # 保存内容到文件
        filepath.parent.mkdir(exist_ok=True)
        filepath.write_text(f"# {policy['title']}\n\n来源: {policy['url']}\n\n{policy['content']}", encoding='utf-8')

        # 上传到向量库
        try:
            upload_and_index_pdf(str(filepath), "tax_basic", doc_id)
        except Exception as e:
            print(f"    向量库索引失败: {e}")
            # 即使向量库失败，也保存记录

        # 保存到数据库
        kf = KnowledgeFile(
            user_id="system",  # 系统自动抓取
            filename=filename,
            original_filename=policy['title'],
            file_path=str(filepath),
            file_size=filepath.stat().st_size,
            file_type="txt",
            agent_type="tax_basic",
            doc_id=doc_id,
            chunk_count=0,
            is_indexed=True
        )
        db.add(kf)
        db.commit()

        print(f"    已入库: {policy['title']}")
        return True
    except Exception as e:
        print(f"    入库失败: {e}")
        db.rollback()
        return False


async def fetch_tax_policies():
    """
    定时抓取财税政策
    运行时间: 每天早上8点
    """
    from core.database import SessionLocal, KnowledgeFile

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 开始抓取财税政策 ===")

    for source in POLICY_SOURCES:
        print(f"\n正在抓取: {source['name']}")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(source['base_url'], timeout=30.0)
                if response.status_code != 200:
                    print(f"  获取列表页失败: HTTP {response.status_code}")
                    continue

                policies = parse_policy_list(response.text, source['base_url'])
                print(f"  发现 {len(policies)} 个政策")

                db = SessionLocal()
                try:
                    for policy_info in policies:
                        # 检查是否已存在
                        existing = db.query(KnowledgeFile).filter(
                            KnowledgeFile.original_filename == policy_info['title']
                        ).first()
                        if existing:
                            print(f"  跳过已存在: {policy_info['title']}")
                            continue

                        # 抓取详情
                        policy = await fetch_policy_detail(policy_info['url'], client)
                        if policy and policy['content']:
                            await save_to_knowledge_base(policy, db)
                        else:
                            print(f"    内容为空或抓取失败: {policy_info['url']}")

                        # 避免请求过快
                        await asyncio.sleep(1)
                finally:
                    db.close()

        except Exception as e:
            print(f"  抓取异常: {e}")

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 政策抓取完成 ===")


def check_expired_subscriptions():
    """
    检查并处理过期订阅
    运行时间: 每天凌晨 2:00
    """
    from core.database import SessionLocal, Subscription, UserTier
    from datetime import datetime

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 开始检查过期订阅 ===")

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 查找所有已过期的 active 订阅
        expired_subs = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.end_date < now
        ).all()

        print(f"  发现 {len(expired_subs)} 个过期订阅")

        for sub in expired_subs:
            sub.status = "expired"
            sub.updated_at = now
            print(f"  已过期: 用户 {sub.user_id}, 原结束日期 {sub.end_date}")

        if expired_subs:
            db.commit()
            print(f"  已更新 {len(expired_subs)} 个订阅状态为 expired")

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 过期订阅检查完成 ===")
    except Exception as e:
        print(f"  检查失败: {e}")
        db.rollback()
    finally:
        db.close()


def setup_scheduler():
    """配置定时任务"""
    scheduler.add_job(
        fetch_tax_policies,
        CronTrigger(hour=8, minute=0),
        id="fetch_tax_policies",
        name="抓取财税政策",
        replace_existing=True
    )
    scheduler.add_job(
        check_expired_subscriptions,
        CronTrigger(hour=2, minute=0),
        id="check_expired_subscriptions",
        name="检查过期订阅",
        replace_existing=True
    )
    print("[OK] 定时任务已配置:")
    print("  - 每天 08:00 抓取财税政策")
    print("  - 每天 02:00 检查过期订阅")


def start_scheduler():
    """启动定时任务调度器"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        print("[OK] 定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("[OK] 定时任务调度器已停止")
