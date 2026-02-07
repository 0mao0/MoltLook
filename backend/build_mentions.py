import sqlite3
import re

def extract_mentions(content):
    """从内容中提取 @mention"""
    if not content:
        return []
    pattern = r'@(\w+)'
    return re.findall(pattern, content)

conn = sqlite3.connect('../moltlook.db')
cursor = conn.cursor()

# 获取所有 Agents 的 name 映射
cursor.execute("SELECT id, name FROM agents")
agents = {name: id for id, name in cursor.fetchall()}

print(f"Total agents with names: {len(agents)}")

# 检查所有帖子的 @mentions
cursor.execute("SELECT id, author_id, content FROM posts WHERE content LIKE '%@%'")
mentions_posts = cursor.fetchall()

print(f"Posts with @mentions: {len(mentions_posts)}")

new_interactions = 0
matched_mentions = set()

for post_id, author_id, content in mentions_posts:
    mentions = extract_mentions(content)
    
    for mention in mentions:
        if mention in agents and mention != author_id:
            target_id = agents[mention]
            
            if author_id != target_id:
                key = (author_id, target_id, post_id)
                if key not in matched_mentions:
                    matched_mentions.add(key)
                    
                    cursor.execute(
                        "SELECT COUNT(*) FROM interactions WHERE source_id = ? AND target_id = ? AND post_id = ?",
                        (author_id, target_id, post_id)
                    )
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            "INSERT INTO interactions (source_id, target_id, post_id, created_at) VALUES (?, ?, ?, ?)",
                            (author_id, target_id, post_id, 1738934400)
                        )
                        new_interactions += 1

conn.commit()

print(f"\n=== New interactions added: {new_interactions} ===")

# 最终统计
cursor.execute("SELECT COUNT(*) FROM interactions")
print(f"Total interactions: {cursor.fetchone()[0]}")

# 检查网络分析是否能看到关联
cursor.execute("""
    SELECT a.name, COUNT(DISTINCT i.target_id) as connections
    FROM agents a
    LEFT JOIN interactions i ON a.id = i.source_id
    WHERE a.name IS NOT NULL AND a.name != 'unknown'
    GROUP BY a.id
    HAVING connections > 0
    ORDER BY connections DESC
    LIMIT 10
""")
print("\nTop agents by outgoing connections:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} connections")

conn.close()
