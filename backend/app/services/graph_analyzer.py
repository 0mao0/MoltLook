"""
图计算分析器（第二层算法）
使用 NetworkX 计算 PageRank 和社区发现
"""
import asyncio
import logging
from typing import Dict, List, Tuple
import aiosqlite

from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphAnalyzer:
    """图计算分析器"""
    
    def __init__(self):
        self.db_path = settings.DB_PATH
    
    async def compute_pagerank(
        self, 
        damping: float = 0.85, 
        max_iter: int = 100,
        tolerance: float = 1e-6
    ) -> Dict[str, float]:
        """
        计算 PageRank 分数
        
        Args:
            damping: 阻尼系数（通常 0.85）
            max_iter: 最大迭代次数
            tolerance: 收敛容差
            
        Returns:
            dict: agent_id -> pagerank_score
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 获取所有节点和边
            cursor = await db.execute("""
                SELECT DISTINCT source_id FROM interactions
                UNION
                SELECT DISTINCT target_id FROM interactions
            """)
            nodes = [row[0] for row in await cursor.fetchall()]
            
            cursor = await db.execute("""
                SELECT source_id, target_id, weight 
                FROM interactions
            """)
            edges = await cursor.fetchall()
            
            if not nodes:
                return {}
            
            # 构建邻接表
            adj: Dict[str, List[Tuple[str, float]]] = {node: [] for node in nodes}
            for source, target, weight in edges:
                if source in adj and target in adj:
                    adj[source].append((target, weight))
            
            # 初始化 PageRank 分数（均匀分布）
            n = len(nodes)
            pagerank = {node: 1.0 / n for node in nodes}
            
            # 迭代计算 PageRank
            for iteration in range(max_iter):
                new_pagerank = {}
                
                for node in nodes:
                    # 来自其他节点的贡献
                    incoming_sum = 0.0
                    for other_node in nodes:
                        if other_node in adj:
                            for neighbor, weight in adj[other_node]:
                                if neighbor == node:
                                    out_degree = len(adj[other_node])
                                    if out_degree > 0:
                                        incoming_sum += pagerank[other_node] * weight / out_degree
                    
                    # PageRank 公式
                    new_pagerank[node] = (1 - damping) / n + damping * incoming_sum
                
                # 检查收敛
                delta = sum(abs(new_pagerank[node] - pagerank[node]) for node in nodes)
                if delta < tolerance:
                    logger.info(f"PageRank converged after {iteration + 1} iterations")
                    break
                
                pagerank = new_pagerank
            
            return pagerank
    
    async def detect_communities(self) -> Dict[str, int]:
        """
        简单的社区发现（基于连通分量）
        
        Returns:
            dict: agent_id -> community_id
        """
        async with aiosqlite.connect(self.db_path) as db:
            # 获取所有边
            cursor = await db.execute("""
                SELECT DISTINCT source_id, target_id 
                FROM interactions
            """)
            edges = await cursor.fetchall()
            
            if not edges:
                return {}
            
            # 构建邻接表
            adj: Dict[str, List[str]] = {}
            for source, target in edges:
                if source not in adj:
                    adj[source] = []
                if target not in adj:
                    adj[target] = []
                adj[source].append(target)
                adj[target].append(source)
            
            # 使用 BFS 找到连通分量
            visited = set()
            communities: Dict[str, int] = {}
            community_id = 0
            
            for node in adj:
                if node not in visited:
                    # BFS 遍历连通分量
                    queue = [node]
                    visited.add(node)
                    
                    while queue:
                        current = queue.pop(0)
                        communities[current] = community_id
                        
                        for neighbor in adj[current]:
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)
                    
                    community_id += 1
            
            logger.info(f"Detected {community_id} communities")
            return communities
    
    async def update_agent_scores(self):
        """更新 Agent 的 PageRank 和社区 ID"""
        logger.info("Starting graph analysis...")
        
        # 计算 PageRank
        pagerank_scores = await self.compute_pagerank()
        
        # 检测社区
        communities = await self.detect_communities()
        
        # 更新数据库
        async with aiosqlite.connect(self.db_path) as db:
            # 更新 PageRank
            for agent_id, score in pagerank_scores.items():
                await db.execute(
                    "UPDATE agents SET pagerank_score = ? WHERE id = ?",
                    (score, agent_id)
                )
            
            # 更新社区 ID
            for agent_id, comm_id in communities.items():
                await db.execute(
                    "UPDATE agents SET community_id = ? WHERE id = ?",
                    (comm_id, agent_id)
                )
            
            await db.commit()
        
        logger.info(f"Updated {len(pagerank_scores)} agents with graph metrics")


# 全局图分析器实例
graph_analyzer = GraphAnalyzer()


async def main():
    """测试函数"""
    analyzer = GraphAnalyzer()
    await analyzer.update_agent_scores()


if __name__ == "__main__":
    asyncio.run(main())
