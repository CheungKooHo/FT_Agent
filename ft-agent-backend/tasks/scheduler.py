"""
定时任务调度器
用于定时抓取财税政策并入库到知识库
"""
import asyncio
import os
import re
import uuid
import httpx
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 定时任务实例
# 用 BackgroundScheduler：不阻塞调用线程，可直接在 FastAPI 启动钩子里使用
scheduler = BackgroundScheduler()

# 不加 UA 会被 chinatax 直接返回 403
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 政策来源配置
# 原配置 https://www.chinatax.gov.cn/clients/newtax/index.html 已失效：
#   - 无 UA 返回 403，带 UA 返回 404
#   - 页面 184 个 <a> 中不含 /claws/ 或 /newtax/，旧解析器结果恒为空
# 现改用财政部「政策发布」栏目：静态 HTML、结构稳定、含 2026 年现行政策。
# chinatax 的 /n810341/n810825/（税收政策库）列表为 JS 动态加载，
# 其后端 /sfc/query.ejf JSON 接口实测 404，故不采用。
POLICY_SOURCES = [
    {
        "name": "财政部",
        "base_url": "http://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/",
        "link_pattern": r'<a[^>]+href="(https?://[^"]*?/t\d{8}_\d+\.html?)"[^>]*>\s*([^<]{8,}?)\s*</a>',
        "content_hint": "TRS_Editor",
    },
]

# 只抓最近 N 天内发布的政策，避免每次都把整页历史文件重抓一遍
# 默认 3650（约 10 年）≈ 不做时间过滤，首次运行即回填列表页上的全部历史文件
_FRESH_DAYS = int(os.getenv("POLICY_FRESH_DAYS", "3650"))


def _clean_text(html: str) -> str:
    """去标签并压缩空白"""
    html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<!--.*?-->', ' ', html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', html)
    for ent, ch in (('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"')):
        text = text.replace(ent, ch)
    lines = [ln.strip() for ln in text.split('\n')]
    return '\n'.join(ln for ln in lines if ln)


def _extract_main_content(html: str, hint: str = None) -> str:
    """优先截取正文容器，取不到再退回全文去标签"""
    if hint:
        m = re.search(re.escape(hint), html)
        if m:
            gt = html.find('>', m.end())
            start = gt + 1 if gt != -1 else m.start()
            tail = html[start:start + 60000]
            stop = re.search(r'(相关文章|【打印】|【关闭】|<!--\s*footer)', tail)
            if stop:
                tail = tail[:stop.start()]
            text = _clean_text(tail)
            if len(text) > 200:
                return text
    return _clean_text(html)


def parse_policy_list(html: str, base_url: str, source_name: str) -> list:
    """从列表页提取政策链接"""
    links = []
    seen = set()
    for source in POLICY_SOURCES:
        if source["name"] != source_name:
            continue
        for m in re.finditer(source["link_pattern"], html, re.IGNORECASE):
            href, title = urljoin(base_url, m.group(1)), m.group(2).strip()
            if not title or href in seen:
                continue
            seen.add(href)
            links.append({"url": href, "title": title})
    return links


def _published_date(url: str, html: str) -> str:
    """从 URL 的 /t20260929_ 或页面正文中取发布日期"""
    m = re.search(r'/t(\d{4})(\d{2})(\d{2})_', url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r'(20\d{2})[-年](\d{1,2})[-月](\d{1,2})', html)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def _is_recent(date_str: str) -> bool:
    if not date_str:
        return True  # 判不出日期时保留，交给去重处理
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return True
    return (datetime.now() - d).days <= _FRESH_DAYS


async def fetch_policy_detail(url: str, client: httpx.AsyncClient, source_name: str) -> dict:
    """抓取单个政策详情页"""
    try:
        response = await client.get(url, timeout=30.0)
        if response.status_code != 200:
            print(f"    跳过（HTTP {response.status_code}）: {url}")
            return None
        response.encoding = 'utf-8'
        html = response.text

        title_match = re.search(r'<title>\s*([^<]+?)\s*</title>', html)
        title = title_match.group(1).strip() if title_match else url
        title = re.sub(r'[_\-—]\s*(中华人民共和国)?(财政部|国家税务总局).*$', '', title).strip() or title

        pub_date = _published_date(url, html)
        if not _is_recent(pub_date):
            return None

        hint = next((s.get("content_hint") for s in POLICY_SOURCES if s["name"] == source_name), None)
        content = _extract_main_content(html, hint)
        if len(content) < 100:
            print(f"    正文过短，跳过: {url}")
            return None

        return {
            "title": title,
            "url": url,
            "content": content[:8000],
            "pub_date": pub_date,
            "source": source_name,
        }
    except Exception as e:
        print(f"    抓取失败: {url} - {e}")
    return None


async def save_to_knowledge_base(policy: dict, db) -> bool:
    """保存政策到知识库

    所有政策入库专业版（tax_pro），超过 6 个月的政策同时进基础版（tax_basic）。
    """
    from core.database import KnowledgeFile
    from core.rag_engine import upload_and_index_pdf
    from datetime import datetime

    try:
        doc_id = str(uuid.uuid4())[:8]
        safe_title = re.sub(r'[^\w\s一-鿿-]', '', policy['title'])[:50]
        filename = f"{safe_title}_{doc_id}.txt"
        filepath = Path(f"./uploads/{filename}")

        filepath.parent.mkdir(exist_ok=True)
        filepath.write_text(
            f"# {policy['title']}\n\n来源: {policy['url']}\n"
            f"发布日期: {policy.get('pub_date') or '未知'}\n\n{policy['content']}",
            encoding='utf-8'
        )

        # 判断是否超过 6 个月
        pub_date_str = policy.get('pub_date')
        is_old = False
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                is_old = (datetime.now() - pub_date).days > 180
            except ValueError:
                pass

        # 始终写入 tax_pro（专业版）
        pro_doc_id = doc_id
        pro_chunks = 0
        try:
            result = upload_and_index_pdf(str(filepath), "tax_pro", pro_doc_id)
            pro_chunks = result.get("chunks", 0)
        except Exception as e:
            print(f"    [tax_pro] 向量库索引失败: {e}")

        kf_pro = KnowledgeFile(
            user_id="system",
            filename=filename,
            original_filename=policy['title'],
            file_path=str(filepath),
            file_size=filepath.stat().st_size,
            file_type="txt",
            agent_type="tax_pro",
            doc_id=pro_doc_id,
            source_url=policy['url'],
            chunk_count=pro_chunks,
            is_indexed=True,
        )
        db.add(kf_pro)

        # 超过 6 个月同时写入 tax_basic（基础版）
        if is_old:
            basic_doc_id = str(uuid.uuid4())[:8]
            basic_chunks = 0
            try:
                result = upload_and_index_pdf(str(filepath), "tax_basic", basic_doc_id)
                basic_chunks = result.get("chunks", 0)
            except Exception as e:
                print(f"    [tax_basic] 向量库索引失败: {e}")

            kf_basic = KnowledgeFile(
                user_id="system",
                filename=filename,
                original_filename=policy['title'],
                file_path=str(filepath),
                file_size=filepath.stat().st_size,
                file_type="txt",
                agent_type="tax_basic",
                doc_id=basic_doc_id,
                source_url=policy['url'],
                chunk_count=basic_chunks,
                is_indexed=True,
            )
            db.add(kf_basic)

        db.commit()
        flag = "[新旧] " if is_old else "[新政策] "
        print(f"    {flag}已入库: {policy['title']} (pro={pro_chunks} chunks, basic={'+' if is_old else '-'}6个月)")
        return True
    except Exception as e:
        print(f"    入库失败: {e}")
        db.rollback()
        return False


async def _fetch_tax_policies_async() -> dict:
    """抓取财税政策并入库（异步实现），返回统计结果"""
    from core.database import SessionLocal, KnowledgeFile

    stats = {"sources": len(POLICY_SOURCES), "found": 0, "saved": 0, "skipped": 0, "failed": 0}
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 开始抓取财税政策 ===")

    for source in POLICY_SOURCES:
        print(f"\n正在抓取: {source['name']}")
        try:
            async with httpx.AsyncClient(timeout=60.0, headers=_HEADERS, follow_redirects=True) as client:
                # 遍历所有列表页（index, index_1, index_2, ...）
                base = source['base_url'].rstrip('/')
                page_idx = 0
                while True:
                    page_url = base if page_idx == 0 else f"{base}/index_{page_idx}.htm"
                    print(f"  抓取列表页 {page_idx}: {page_url}")
                    response = await client.get(page_url, timeout=30.0)
                    response.encoding = 'utf-8'
                    if response.status_code != 200:
                        print(f"    列表页 {page_idx} 获取失败: HTTP {response.status_code}")
                        break

                    policies = parse_policy_list(response.text, source['base_url'], source['name'])
                    if not policies:
                        print(f"    列表页 {page_idx} 无政策链接，停止翻页")
                        break

                    stats["found"] += len(policies)
                    print(f"    发现 {len(policies)} 条链接")

                    db = SessionLocal()
                    try:
                        for policy_info in policies:
                            existing = db.query(KnowledgeFile).filter(
                                KnowledgeFile.source_url == policy_info['url']
                            ).first()
                            if existing:
                                stats["skipped"] += 1
                                continue

                            policy = await fetch_policy_detail(policy_info['url'], client, source['name'])
                            if policy and policy['content']:
                                if await save_to_knowledge_base(policy, db):
                                    stats["saved"] += 1
                                else:
                                    stats["failed"] += 1
                            else:
                                stats["skipped"] += 1

                            await asyncio.sleep(0.5)
                    finally:
                        db.close()

                    page_idx += 1

        except Exception as e:
            print(f"  抓取异常: {e}")
            stats["failed"] += 1

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 政策抓取完成 === {stats}")
    return stats


def fetch_tax_policies() -> dict:
    """定时抓取财税政策（同步入口）

    必须是同步函数：APScheduler 在线程池中执行任务，不会 await 协程。
    原先声明为 async def，触发时只构造协程对象随即丢弃（RuntimeWarning:
    coroutine was never awaited），正文一行都不会执行。
    """
    return asyncio.run(_fetch_tax_policies_async())


def check_expiring_subscriptions():
    """
    检查即将到期的订阅并发送提醒通知，同时处理已过期订阅
    运行时间: 每天早上 9:00
    """
    from core.database import SessionLocal, Subscription, Notification, User
    from services.email import EmailService
    from datetime import datetime, timedelta

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 开始检查订阅状态 ===")

    email_service = EmailService.get_instance()
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        three_days_later = now + timedelta(days=3)

        expired_subs = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.end_date < now
        ).all()
        if expired_subs:
            for sub in expired_subs:
                sub.status = "expired"
                sub.updated_at = now
                print(f"  已过期: 用户 {sub.user_id}, 原结束日期 {sub.end_date}")
            db.commit()
            print(f"  已更新 {len(expired_subs)} 个订阅状态为 expired")

        expiring_subs = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.end_date > now,
            Subscription.end_date <= three_days_later
        ).all()
        print(f"  发现 {len(expiring_subs)} 个即将到期订阅")

        for sub in expiring_subs:
            existing = db.query(Notification).filter(
                Notification.user_id == sub.user_id,
                Notification.notification_type == "subscription_expiring",
                Notification.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
            ).first()
            if existing:
                continue

            notification = Notification(
                user_id=sub.user_id,
                notification_type="subscription_expiring",
                title="订阅即将到期",
                content=f"您的订阅将在 {sub.end_date.strftime('%Y-%m-%d')} 到期，为避免服务中断，请及时续费。",
                is_read=False
            )
            db.add(notification)

            user = db.query(User).filter(User.user_id == sub.user_id).first()
            if user and user.email:
                email_service.send_subscription_expiring_notification(
                    user.email,
                    user.username,
                    sub.end_date.strftime('%Y-%m-%d')
                )

            print(f"  已提醒: 用户 {sub.user_id}, 到期日期 {sub.end_date}")

        if expiring_subs:
            db.commit()

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === 订阅状态检查完成 ===")
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
        check_expiring_subscriptions,
        CronTrigger(hour=9, minute=0),
        id="check_expiring_subscriptions",
        name="检查即将到期订阅",
        replace_existing=True
    )
    print("[OK] 定时任务已配置:")
    print("  - 每天 08:00 抓取财税政策")
    print("  - 每天 09:00 检查即将到期订阅并发送提醒")


def start_scheduler():
    """启动定时任务调度器"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        print("[OK] 定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[OK] 定时任务调度器已停止")
