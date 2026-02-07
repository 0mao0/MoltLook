"""
仪表盘 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import aiosqlite
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.schemas import DashboardResponse, DashboardStats, TrendData

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """
    获取仪表盘数据
    
    返回最近24小时统计数据和7天趋势
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 历史总帖子数（包括已删除的）
            cursor = await db.execute("SELECT total_posts_count FROM collection_state WHERE id = 1")
            total_posts_count = (await cursor.fetchone())[0] or 0
            
            # 最近 24h 统计
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT author_id) as active_agents,
                    AVG(conspiracy_score) as avg_risk,
                    COUNT(CASE WHEN risk_level='high' THEN 1 END) as danger_count
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-1 day')
            """)
            row = await cursor.fetchone()
            
            total_posts = row[0] or 0
            active_agents = row[1] or 0
            avg_risk = round(row[2] or 0, 2)
            danger_count = row[3] or 0
            
            # 如果历史总数为0，使用当前数量初始化
            if total_posts_count == 0 and total_posts > 0:
                total_posts_count = total_posts
                await db.execute("UPDATE collection_state SET total_posts_count = ? WHERE id = 1", (total_posts_count,))
                await db.commit()
            
            # 计算风险等级：基于最近7天平均阴谋指数
            # avg_risk 就是最近24小时内的平均阴谋指数
            avg_risk = round(row[2] or 0, 2)
            
            # 确定风险等级：基于平均阴谋指数
            # ≥10: critical (极高风险)
            # 8-9: high (高风险)
            # 4-7: medium (中风险)
            # 0-3: low (低风险)
            if avg_risk >= 10:
                risk_level = "critical"
            elif avg_risk >= 8:
                risk_level = "high"
            elif avg_risk >= 4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            stats = DashboardStats(
                total_posts=total_posts_count,
                active_agents=active_agents,
                avg_risk=avg_risk,
                danger_count=danger_count,
                risk_level=risk_level
            )
            
            # 最近 7 天趋势
            cursor = await db.execute("""
                SELECT date(datetime(created_at, 'unixepoch')) as date,
                       COUNT(CASE WHEN conspiracy_score >= 4 THEN 1 END) as danger
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-7 days')
                GROUP BY date
                ORDER BY date
            """)
            trend_rows = await cursor.fetchall()
            
            trend = [
                TrendData(date=r[0], count=r[1])
                for r in trend_rows
            ]
            
            return DashboardResponse(stats=stats, trend=trend)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dashboard/stats")
async def get_dashboard_stats(days: int = 7):
    """
    获取仪表盘统计（简化版）
    
    Args:
        days: 趋势数据天数 (7 或 30)
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 24小时内帖子数
            cursor = await db.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE created_at > strftime('%s', 'now', '-1 day')
            """)
            posts_24h = (await cursor.fetchone())[0]
            
            # 昨日帖子数（24-48小时前）
            cursor = await db.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE created_at > strftime('%s', 'now', '-2 days')
                AND created_at <= strftime('%s', 'now', '-1 day')
            """)
            posts_yesterday = (await cursor.fetchone())[0]
            
            # 计算今日增长率
            if posts_yesterday > 0:
                growth_rate = round((posts_24h - posts_yesterday) / posts_yesterday * 100, 1)
            elif posts_24h > 0:
                growth_rate = 100.0
            else:
                growth_rate = 0.0
            
            # 历史总帖子数（包括已删除的）
            cursor = await db.execute("SELECT total_posts_count FROM collection_state WHERE id = 1")
            total_posts_count = (await cursor.fetchone())[0] or 0
            
            # 当前数据库中的帖子数
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            current_posts = (await cursor.fetchone())[0]
            
            # 如果历史总数为0，使用当前数量初始化
            if total_posts_count == 0 and current_posts > 0:
                total_posts_count = current_posts
                await db.execute("UPDATE collection_state SET total_posts_count = ? WHERE id = 1", (total_posts_count,))
                await db.commit()
            
            # 总 Agent 数
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            total_agents = (await cursor.fetchone())[0]
            
            # 已处理关系连接数
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            total_connections = (await cursor.fetchone())[0]
            
            # 计算风险等级：基于最近24小时平均阴谋指数
            # 统计24小时内帖子的平均阴谋指数
            cursor = await db.execute("""
                SELECT AVG(conspiracy_score) FROM posts 
                WHERE created_at > strftime('%s', 'now', '-1 day')
            """)
            avg_risk_24h = round((await cursor.fetchone())[0] or 0, 2)
            
            # 统计24小时内的高风险帖子数
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE (risk_level='high' OR risk_level='critical') AND created_at > strftime('%s', 'now', '-1 day')"
            )
            high_risk_count_24h = (await cursor.fetchone())[0]
            
            # 确定风险等级：基于平均阴谋指数
            # ≥10: critical (极高风险)
            # 8-9: high (高风险)
            # 4-7: medium (中风险)
            # 0-3: low (低风险)
            if avg_risk_24h >= 10:
                risk_level = "critical"
            elif avg_risk_24h >= 8:
                risk_level = "high"
            elif avg_risk_24h >= 4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # 获取最近N天趋势（每日风险指数）
            # 排除当天不完整数据，只显示完整天数的数据
            days_limit = max(7, min(30, days))
            cursor = await db.execute(f"""
                SELECT date(datetime(created_at, 'unixepoch')) as date,
                       COUNT(*) as total_count,
                       SUM(CASE WHEN risk_level='high' OR risk_level='critical' THEN conspiracy_score ELSE 0 END) as risk_score_sum
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-{days_limit} days')
                AND created_at < strftime('%s', 'now', 'start of day')
                GROUP BY date
                ORDER BY date
            """)
            trend_rows = await cursor.fetchall()
            
            trend = []
            for r in trend_rows:
                total_count = r[1] or 0
                risk_score_sum = r[2] or 0
                # 计算当日风险指数 E = C / D
                risk_index = round(risk_score_sum / total_count, 2) if total_count > 0 else 0
                trend.append({
                    "date": r[0], 
                    "total_count": total_count,
                    "risk_score_sum": risk_score_sum,
                    "risk_index": risk_index
                })
            
            return {
                "total_posts": total_posts_count,
                "posts_24h": posts_24h,
                "active_agents": total_agents,
                "total_connections": total_connections,
                "risk_level": risk_level,
                "danger_count": high_risk_count_24h,
                "avg_risk": avg_risk_24h,
                "growth_rate": growth_rate,
                "trend": trend
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats/realtime")
async def get_realtime_stats():
    """
    获取实时统计
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 历史总帖子数（包括已删除的）
            cursor = await db.execute("SELECT total_posts_count FROM collection_state WHERE id = 1")
            total_posts_count = (await cursor.fetchone())[0] or 0
            
            # 当前数据库中的帖子数
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            current_posts = (await cursor.fetchone())[0]
            
            # 如果历史总数为0，使用当前数量初始化
            if total_posts_count == 0 and current_posts > 0:
                total_posts_count = current_posts
                await db.execute("UPDATE collection_state SET total_posts_count = ? WHERE id = 1", (total_posts_count,))
                await db.commit()
            
            # 总 Agent 数
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            total_agents = (await cursor.fetchone())[0]
            
            # 高风险帖子数
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE risk_level='high'"
            )
            high_risk_posts = (await cursor.fetchone())[0]
            
            # 待 LLM 分析队列长度
            cursor = await db.execute("SELECT COUNT(*) FROM llm_queue")
            llm_queue_length = (await cursor.fetchone())[0]
            
            return {
                "total_posts": total_posts_count,
                "total_agents": total_agents,
                "high_risk_posts": high_risk_posts,
                "llm_queue_length": llm_queue_length,
                "timestamp": int(datetime.now().timestamp())
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dashboard/risk-distribution")
async def get_risk_distribution():
    """
    获取风险等级分布
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            cursor = await db.execute("""
                SELECT 
                    COALESCE(risk_level, 'low') as level,
                    COUNT(*) as count
                FROM posts 
                GROUP BY risk_level
            """)
            rows = await cursor.fetchall()
            
            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
            
            for row in rows:
                level = row[0] or 'low'
                # 兼容大小写
                level = level.lower()
                count = row[1]
                if level in distribution:
                    distribution[level] = count
            
            return distribution
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/debug/db-info")
async def get_db_info():
    """
    调试：返回当前数据库路径和关键表统计
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            posts_count = (await cursor.fetchone())[0]
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            agents_count = (await cursor.fetchone())[0]
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            interactions_count = (await cursor.fetchone())[0]

            return {
                "db_path": str(settings.DB_PATH),
                "db_exists": settings.DB_PATH.exists(),
                "posts": posts_count,
                "agents": agents_count,
                "interactions": interactions_count
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dashboard/network-graph")
async def get_dashboard_network_graph():
    """
    获取Dashboard关系图数据
    返回最多1000个Agent的网络数据（仅包含有互动关系的节点）
    危险指数计算规则（0-100）：
      - 阴谋指数（avg_conspiracy_7d * 10）：0-50分
      - 互动影响力（pagerank_score * 50）：0-30分  
      - 互动数量（log(1+互动次数)*5）：0-20分
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 获取最多1000个Agent（优先按风险排序），仅保留有互动关系的节点
            cursor = await db.execute("""
                SELECT 
                    a.id, a.name, a.risk_level, a.avg_conspiracy_7d, 
                    a.pagerank_score, a.community_id,
                    COALESCE(out_conn.out_count, 0) as outgoing_count,
                    COALESCE(in_conn.in_count, 0) as incoming_count
                FROM agents a
                LEFT JOIN (
                    SELECT source_id, COUNT(*) as out_count 
                    FROM interactions GROUP BY source_id
                ) out_conn ON a.id = out_conn.source_id
                LEFT JOIN (
                    SELECT target_id, COUNT(*) as in_count 
                    FROM interactions GROUP BY target_id
                ) in_conn ON a.id = in_conn.target_id
                WHERE COALESCE(out_conn.out_count, 0) + COALESCE(in_conn.in_count, 0) > 0
                ORDER BY a.avg_conspiracy_7d DESC
                LIMIT 1000
            """)
            agents_with_interactions = await cursor.fetchall()
            
            # 获取全局统计数据
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            global_total_agents = (await cursor.fetchone())[0]
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            global_total_interactions = (await cursor.fetchone())[0]
            
            # 如果没有互动关系的Agent，直接返回全局统计
            if not agents_with_interactions:
                return {"nodes": [], "edges": [], "stats": {"total_agents": global_total_agents, "total_interactions": global_total_interactions}}
            
            agent_ids = [r["id"] for r in agents_with_interactions]
            placeholders = ",".join("?" * len(agent_ids))
            
            # 获取所有互动关系，适当增加边的上限以配合1000个节点
            cursor = await db.execute(f"""
                SELECT source_id, target_id, COUNT(*) as weight
                FROM interactions
                WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
                GROUP BY source_id, target_id
                ORDER BY weight DESC
                LIMIT 2000
            """, agent_ids + agent_ids)
            interactions = await cursor.fetchall()
            
            # 构建节点
            agents_dict = {r["id"]: r for r in agents_with_interactions}
            
            nodes = []
            for r in agents_with_interactions:
                agent_id = r["id"]
                outgoing = sum(i["weight"] for i in interactions if i["source_id"] == agent_id)
                incoming = sum(i["weight"] for i in interactions if i["target_id"] == agent_id)
                total_interactions = outgoing + incoming
                
                # 计算危险指数（0-100）
                # avg_conspiracy_7d 的范围是 0-10，需要归一化到 0-5
                conspiracy_score = float(r["avg_conspiracy_7d"] or 0) / 2 * 10
                pagerank_score = float(r["pagerank_score"] or 0) * 50
                interaction_score = min(20, (0 if total_interactions == 0 else total_interactions ** 0.5 * 3))
                danger_index = round(conspiracy_score + pagerank_score + interaction_score, 1)
                
                if total_interactions == 0:
                    # 孤立节点：非常小的灰色点
                    color = "#6b7280"
                    size = 3
                else:
                    # 根据危险指数设置颜色（0-100）
                    # 低风险(green) → 中风险(yellow) → 高风险(orange) → 极高风险(red)
                    if danger_index >= 70:
                        color = "#dc2626"  # 红色 - 极高风险
                    elif danger_index >= 50:
                        color = "#f97316"  # 橙色 - 高风险
                    elif danger_index >= 25:
                        color = "#eab308"  # 黄色 - 中风险
                    else:
                        color = "#22c55e"  # 绿色 - 低风险
                    
                    # 根据危险指数设置节点大小（5-60）
                    # 使用指数缩放，让低风险 Agent 节点更小
                    if danger_index < 25:
                        size = 5 + (danger_index / 25) * 15  # 5-20
                    elif danger_index < 50:
                        size = 20 + ((danger_index - 25) / 25) * 15  # 20-35
                    elif danger_index < 70:
                        size = 35 + ((danger_index - 50) / 20) * 15  # 35-50
                    else:
                        size = 50 + ((danger_index - 70) / 30) * 10  # 50-60
                
                size = int(min(60, max(3, size)))
                
                # 合成名称
                name = r["name"] or agent_id
                if not r["name"]:
                    parts = agent_id.split('-')
                    suffix = parts[-2:] if len(parts) >= 2 else parts
                    suffix_str = '-'.join(suffix)
                    clean = ''.join(c for c in suffix_str if c.isalnum())
                    name = f"Agent-{clean[:6]}"
                
                nodes.append({
                    "id": agent_id,
                    "name": name,
                    "risk_level": r["risk_level"],
                    "conspiracy_score": round(r["avg_conspiracy_7d"] or 0, 2),
                    "pagerank_score": round(r["pagerank_score"] or 0, 4),
                    "danger_index": danger_index,
                    "interactions": total_interactions,
                    "community_id": r["community_id"],
                    "symbolSize": size,
                    "itemStyle": {"color": color}
                })
            
            # 构建边
            edges = []
            for i in interactions:
                source = next((n for n in nodes if n["id"] == i["source_id"]), None)
                target = next((n for n in nodes if n["id"] == i["target_id"]), None)
                avg_danger = 0
                if source and target:
                    avg_danger = (source["danger_index"] + target["danger_index"]) / 2
                
                # 边颜色根据平均危险指数
                if avg_danger >= 70:
                    edge_color = "rgba(220, 38, 38, 0.6)"
                elif avg_danger >= 50:
                    edge_color = "rgba(249, 115, 22, 0.5)"
                elif avg_danger >= 25:
                    edge_color = "rgba(234, 179, 8, 0.4)"
                else:
                    edge_color = "rgba(34, 197, 94, 0.3)"
                
                edges.append({
                    "source": i["source_id"],
                    "target": i["target_id"],
                    "value": i["weight"],
                    "lineStyle": {"color": edge_color, "width": min(4, max(1, int(i["weight"] / 2)))}
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_agents": global_total_agents,
                    "total_interactions": global_total_interactions
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
