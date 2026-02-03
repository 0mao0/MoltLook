"""
生成模拟互动数据的脚本
用于演示 connections 功能
"""
import sqlite3
import random
import time

DB_PATH = 'moltlook.db'

def generate_mock_interactions():
    """生成模拟的互动关系"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有 agent 和他们的帖子
    cursor.execute('''
        SELECT DISTINCT a.id, a.name, COUNT(p.id) as post_count
        FROM agents a
        JOIN posts p ON a.id = p.author_id
        GROUP BY a.id
        HAVING post_count >= 2
        LIMIT 50
    ''')
    agents = cursor.fetchall()
    
    if len(agents) < 2:
        print('没有足够的 agent 来生成互动关系')
        conn.close()
        return
    
    print(f'找到 {len(agents)} 个有帖子的 agent')
    
    # 清空现有的互动数据
    cursor.execute('DELETE FROM interactions')
    
    interactions_created = 0
    
    # 为每个 agent 生成 1-5 个互动关系
    for agent in agents:
        agent_id = agent[0]
        num_interactions = random.randint(1, min(5, len(agents) - 1))
        
        # 随机选择其他 agent 作为互动对象
        other_agents = [a[0] for a in agents if a[0] != agent_id]
        random.shuffle(other_agents)
        
        for i in range(num_interactions):
            target_id = other_agents[i]
            
            # 获取该 agent 的一个帖子作为互动依据
            cursor.execute(
                'SELECT id, created_at FROM posts WHERE author_id = ? ORDER BY RANDOM() LIMIT 1',
                (agent_id,)
            )
            post = cursor.fetchone()
            
            if post:
                post_id = post[0]
                created_at = post[1] - random.randint(0, 86400 * 7)  # 7 天内的随机时间
                
                # 检查是否已存在
                cursor.execute(
                    'SELECT id FROM interactions WHERE source_id = ? AND target_id = ?',
                    (agent_id, target_id)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        '''INSERT INTO interactions 
                           (source_id, target_id, post_id, weight, created_at)
                           VALUES (?, ?, ?, ?, ?)''',
                        (agent_id, target_id, post_id, random.uniform(0.5, 2.0), created_at)
                    )
                    interactions_created += 1
    
    conn.commit()
    
    # 更新 agents 表的 reply_count 和 be_replied_count
    cursor.execute('''
        UPDATE agents 
        SET reply_count = (
            SELECT COUNT(*) FROM interactions WHERE source_id = agents.id
        ),
        be_replied_count = (
            SELECT COUNT(*) FROM interactions WHERE target_id = agents.id
        )
    ''')
    
    conn.commit()
    
    # 验证
    cursor.execute('SELECT COUNT(*) FROM interactions')
    total = cursor.fetchone()[0]
    
    print(f'成功创建 {interactions_created} 条互动关系')
    print(f'interactions 表总记录数: {total}')
    
    # 显示一些示例
    print('\n示例互动关系:')
    cursor.execute('''
        SELECT i.source_id, i.target_id, i.count, a1.name as source_name, a2.name as target_name
        FROM (
            SELECT source_id, target_id, COUNT(*) as count
            FROM interactions
            GROUP BY source_id, target_id
        ) i
        JOIN agents a1 ON i.source_id = a1.id
        JOIN agents a2 ON i.target_id = a2.id
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        print(f'  {row[3][:20]}... -> {row[4][:20]}... : {row[2]} 次互动')
    
    conn.close()

if __name__ == '__main__':
    generate_mock_interactions()
