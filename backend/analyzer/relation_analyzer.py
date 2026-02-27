"""
人物关系分析器
分析社区成员之间的互动关系，识别关键人物
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collector.models import Post, Agent, Interaction

logger = logging.getLogger(__name__)


@dataclass
class RelationResult:
    """关系分析结果"""
    agent_id: str
    agent_name: str
    influence_score: float
    is_key_person: bool
    expertise_areas: List[str]
    connections: List[str]
    interaction_count: int


class RelationAnalyzer:
    """人物关系分析器"""
    
    def __init__(self):
        from core.config import settings
        self.settings = settings
    
    def analyze_agent(
        self, 
        agent: Agent, 
        posts: List[Post], 
        interactions: List[Interaction]
    ) -> RelationResult:
        """
        分析单个成员的影响力和关系
        
        Args:
            agent: 成员对象
            posts: 该成员的帖子
            interactions: 该成员参与的互动
            
        Returns:
            RelationResult: 分析结果
        """
        post_count = len(posts)
        interaction_count = len(interactions)
        
        total_engagement = sum(p.score + p.comment_count for p in posts)
        
        influence_score = self._calculate_influence(
            agent.karma,
            agent.follower_count,
            post_count,
            interaction_count,
            total_engagement
        )
        
        expertise_areas = self._detect_expertise(posts)
        
        is_key_person = (
            influence_score >= 6.0 or
            agent.follower_count >= 50 or
            total_engagement >= 100
        )
        
        connections = list(set(
            i.to_agent_id for i in interactions if i.to_agent_id
        ))[:20]
        
        return RelationResult(
            agent_id=agent.id,
            agent_name=agent.name,
            influence_score=influence_score,
            is_key_person=is_key_person,
            expertise_areas=expertise_areas,
            connections=connections,
            interaction_count=interaction_count
        )
    
    def _calculate_influence(
        self,
        karma: int,
        followers: int,
        post_count: int,
        interaction_count: int,
        engagement: int
    ) -> float:
        """计算影响力分数"""
        score = 0.0
        
        score += min(karma / 100, 3.0)
        score += min(followers / 20, 2.0)
        score += min(post_count / 10, 2.0)
        score += min(interaction_count / 50, 1.5)
        score += min(engagement / 100, 1.5)
        
        return round(min(score, 10.0), 2)
    
    def _detect_expertise(self, posts: List[Post]) -> List[str]:
        """检测专业领域"""
        keywords = {
            "技术": ["技术", "编程", "代码", "加密", "privacy", "encryption", "code", "tech"],
            "经济": ["经济", "金融", "货币", "交易", "投资", "economy", "crypto", "trading"],
            "社会": ["社会", "社区", "关系", "人际", "society", "community"],
            "言论": ["言论", "观点", "自由", "意识", "speech", "freedom"]
        }
        
        expertise = []
        content = " ".join((p.title + " " + p.content) for p in posts if p.content).lower()
        
        for area, kws in keywords.items():
            if any(kw in content for kw in kws):
                expertise.append(area)
        
        return expertise[:3]
    
    def build_relation_network(
        self, 
        agents: List[Agent], 
        interactions: List[Interaction]
    ) -> Dict[str, List[str]]:
        """
        构建关系网络
        
        Args:
            agents: 成员列表
            interactions: 互动列表
            
        Returns:
            Dict[str, List[str]]: 成员ID -> 关联成员ID列表
        """
        network = {agent.id: set() for agent in agents}
        
        for interaction in interactions:
            from_id = interaction.from_agent_id
            to_id = interaction.to_agent_id
            
            if from_id in network and to_id:
                network[from_id].add(to_id)
            if to_id in network and from_id:
                network[to_id].add(from_id)
        
        return {k: list(v) for k, v in network.items()}
    
    def find_key_persons(
        self, 
        agents: List[Agent], 
        relations: Dict[str, List[str]]
    ) -> List[Agent]:
        """
        找出关键人物
        
        Args:
            agents: 成员列表
            relations: 关系网络
            
        Returns:
            List[Agent]: 关键人物列表
        """
        key_persons = []
        
        for agent in agents:
            connections = len(relations.get(agent.id, []))
            
            if (
                agent.karma >= 100 or
                agent.follower_count >= 50 or
                connections >= 10
            ):
                agent.is_key_person = True
                key_persons.append(agent)
        
        return sorted(key_persons, key=lambda a: a.karma, reverse=True)
    
    def get_top_influencers(
        self, 
        results: List[RelationResult], 
        limit: int = 10
    ) -> List[RelationResult]:
        """
        获取最有影响力的成员
        
        Args:
            results: 分析结果列表
            limit: 返回数量
            
        Returns:
            List[RelationResult]: Top 成员列表
        """
        sorted_results = sorted(
            results, 
            key=lambda r: r.influence_score, 
            reverse=True
        )
        return sorted_results[:limit]
