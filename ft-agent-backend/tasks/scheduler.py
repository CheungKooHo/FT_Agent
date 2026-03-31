"""
定时任务调度器
用于定时抓取财税政策等
"""
import asyncio
import httpx
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 定时任务实例
scheduler = AsyncIOScheduler()


async def fetch_tax_policies():
    """
    定时抓取财税政策
    运行时间: 每天早上8点
    """
    print(f"[{datetime.now()}] 开始抓取财税政策...")

    # 需要配置的政策源URL列表
    # 实际实现需要根据具体来源调整
    sources = [
        # 国家税务总局
        "https://www.chinatax.gov.cn/claws/newtax/index.html",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in sources:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    # 解析政策列表页
                    # 具体解析逻辑根据页面结构调整
                    print(f"  成功获取: {url}")
                else:
                    print(f"  获取失败 {url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  抓取异常 {url}: {e}")

    print(f"[{datetime.now()}] 政策抓取完成")


def setup_scheduler():
    """配置定时任务"""
    # 每天早上8点执行
    scheduler.add_job(
        fetch_tax_policies,
        CronTrigger(hour=8, minute=0),
        id="fetch_tax_policies",
        name="抓取财税政策",
        replace_existing=True
    )
    print("✓ 定时任务已配置: 每天 8:00 抓取财税政策")


def start_scheduler():
    """启动定时任务调度器"""
    if not scheduler.running:
        scheduler.start()
        print("✓ 定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("✓ 定时任务调度器已停止")
