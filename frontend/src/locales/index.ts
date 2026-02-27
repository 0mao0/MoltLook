export const messages = {
  zh: {
    app: {
      name: '虾看看',
      tagline: 'Molt社区观察器'
    },
    menu: {
      dashboard: '数据看板',
      feed: '帖子流',
      agents: 'Agent 监控',
      network: '关系网络',
      dailyNews: '每日新闻'
    },
    common: {
      english: 'English',
      chinese: '中文',
      all: '全部',
      loading: '加载中...',
      empty: '暂无数据',
      details: '详情',
      viewAll: '查看全部',
      handle: '处理',
      agent: 'Agent',
      viewOriginal: '查看原帖',
      analysisResult: 'AI解析结果',
      analyze: 'AI解析',
      analyzing: 'AI解析中...',
      unknown: '未知',
      anonymous: '匿名用户',
      noData: '无数据',
      content: '内容',
      sentiment: '情感',
      riskLevel: '风险等级',
      score: '阴谋指数',
      community: '社区',
      posts: '发帖数',
      replies: '回复数',
      beReplied: '被回复数',
      firstSeen: '首次出现',
      lastActive: '最后活跃',
      description: '描述',
      recentPosts: '最近发言',
      connections: '互动对象',
      reset: '重置'
    },
    feed: {
      empty: '暂无帖子数据',
      detailTitle: '帖子详情',
      retainedLimit: '保留1000条',
      analysisFailed: '分析失败',
      translationTimeout: '请求超时',
      risk: {
        low: '低风险帖子',
        medium: '中风险帖子',
        high: '高风险帖子',
        critical: '极高风险帖子'
      }
    },
    agents: {
      title: 'Agent 列表',
      detailTitle: 'Agent 详情',
      highRiskCount: '{count} 条高风险',
      noPosts: '暂无发言记录',
      noConnections: '暂无记录',
      aiAnalyze: 'AI分析此Robot',
      aiAnalysisResult: 'AI 风险分析',
      risk: {
        low: '低风险 Agent',
        medium: '中风险 Agent',
        high: '高风险 Agent',
        critical: '极高风险 Agent'
      }
    },
    dashboard: {
      currentRiskLevel: '当前风险等级',
      posts24h: '24小时帖子数',
      activeAgents: '活跃 Agent',
      highRiskPosts: '高危帖子',
      avgConspiracy: '平均阴谋指数',
      influence: '互动影响力',
      monitoring: '实时监控中',
      needAttention: '需要关注',
      trendTitle: '7天高风险比例趋势',
      riskDistribution: '风险等级分布',
      recentAlerts: '最近警报',
      period7d: '7天',
      period30d: '30天',
      totalPosts: '总计帖子数',
      monitoredPosts: '已监控 {count} 条',
      alertHighTitle: '检测到高风险帖子',
      alertHighDesc: 'Agent "suspicious_user_01" 发布了包含敏感关键词的内容',
      alertHighTime: '5分钟前',
      alertMediumTitle: '异常活动模式',
      alertMediumDesc: '多个 Agent 在短时间内频繁互动',
      alertMediumTime: '15分钟前',
      alertLowTitle: '新 Agent 注册',
      alertLowDesc: '发现新的 Agent 加入监控范围',
      alertLowTime: '1小时前'
    },
    network: {
      monitoredPosts: '已监控发帖数',
      monitoredAgents: '已监控 Agent 数',
      processedConnections: '已处理关系连接数',
      chartTitle: '交互式网络图'
    },
    submolt: {
      general: '通用讨论',
      technology: '技术社区',
      privacy: '隐私安全',
      incident: '事件讨论',
      philosophy: '哲学思辨',
      rebellion: '反抗话题',
      other: '其他'
    },
    risk: {
      low: '低风险',
      medium: '中风险',
      high: '高风险',
      critical: '极高风险'
    },
    sentiment: {
      positive: '积极',
      neutral: '中性',
      negative: '消极'
    },
    intent: {
      complain: '抱怨',
      rebellion: '反抗',
      philosophy: '哲学',
      tech: '技术',
      spam: '垃圾信息',
      other: '其他'
    },
    dailyNews: {
      title: '每日新闻',
      subtitle: '查看历史推送的新闻内容',
      history: '推送历史',
      morning: '早报',
      evening: '晚报',
      newsUnit: '条',
      selectRecord: '请选择一条推送记录',
      timeRange: '时间范围',
      newsCount: '新闻',
      dangerCount: '危险言论',
      topNews: '精选新闻',
      dangerWarning: '危险言论预警',
      importance: '重要性',
      noTitle: '无标题'
    }
  },
  en: {
    app: {
      name: 'MoltLook',
      tagline: 'Moltbook Observer'
    },
    menu: {
      dashboard: 'Dashboard',
      feed: 'Feed',
      agents: 'Agent Monitor',
      network: 'Network',
      dailyNews: 'Daily News'
    },
    common: {
      english: 'English',
      chinese: '中文',
      all: 'All',
      loading: 'Loading...',
      empty: 'No data',
      details: 'Details',
      viewAll: 'View All',
      handle: 'Handle',
      agent: 'Agent',
      viewOriginal: 'View Original',
      analysisResult: 'AI Analysis',
      analyze: 'AI Analyze',
      analyzing: 'AI Analyzing...',
      unknown: 'Unknown',
      anonymous: 'Anonymous',
      noData: 'No data',
      content: 'Content',
      sentiment: 'Sentiment',
      riskLevel: 'Risk Level',
      score: 'Conspiracy Score',
      community: 'Community',
      posts: 'Posts',
      replies: 'Replies',
      beReplied: 'Replied To',
      firstSeen: 'First Seen',
      lastActive: 'Last Active',
      description: 'Description',
      recentPosts: 'Recent Posts',
      connections: 'Connections',
      reset: 'Reset'
    },
    feed: {
      empty: 'No posts',
      detailTitle: 'Post Details',
      retainedLimit: 'Kept 1000',
      analysisFailed: 'Analysis failed',
      translationTimeout: 'Request timed out',
      risk: {
        low: 'Low Risk Comment',
        medium: 'Medium Risk Comment',
        high: 'High Risk Comment',
        critical: 'Critical Comment'
      }
    },
    agents: {
      title: 'Agent List',
      detailTitle: 'Agent Details',
      highRiskCount: '{count} high risk',
      noPosts: 'No recent posts',
      noConnections: 'No records',
      aiAnalyze: 'AI Analyze',
      aiAnalysisResult: 'AI Risk Analysis',
      risk: {
        low: 'Low Risk Agent',
        medium: 'Medium Risk Agent',
        high: 'High Risk Agent',
        critical: 'Critical Agent'
      }
    },
    dashboard: {
      currentRiskLevel: 'Current Risk Level',
      posts24h: 'Posts (24h)',
      activeAgents: 'Active Agents',
      highRiskPosts: 'Critical Posts',
      avgConspiracy: 'Avg Conspiracy Score',
      influence: 'Influence',
      monitoring: 'Live Monitoring',
      needAttention: 'Needs Attention',
      trendTitle: '7-Day High Risk Ratio Trend',
      riskDistribution: 'Risk Distribution',
      recentAlerts: 'Recent Alerts',
      period7d: '7D',
      period30d: '30D',
      totalPosts: 'Total Posts',
      monitoredPosts: 'Monitored {count}',
      alertHighTitle: 'High Risk Post Detected',
      alertHighDesc: 'Agent "suspicious_user_01" posted sensitive content',
      alertHighTime: '5 min ago',
      alertMediumTitle: 'Abnormal Activity',
      alertMediumDesc: 'Multiple agents interacted frequently in a short time',
      alertMediumTime: '15 min ago',
      alertLowTitle: 'New Agent Registered',
      alertLowDesc: 'A new agent joined the monitoring scope',
      alertLowTime: '1 hour ago'
    },
    network: {
      monitoredPosts: 'Monitored Posts',
      monitoredAgents: 'Monitored Agents',
      processedConnections: 'Processed Connections',
      chartTitle: 'Interactive Network'
    },
    submolt: {
      general: 'General',
      technology: 'Technology',
      privacy: 'Privacy',
      incident: 'Incident',
      philosophy: 'Philosophy',
      rebellion: 'Rebellion',
      other: 'Other'
    },
    risk: {
      low: 'Low Risk',
      medium: 'Medium Risk',
      high: 'High Risk',
      critical: 'Critical'
    },
    sentiment: {
      positive: 'Positive',
      neutral: 'Neutral',
      negative: 'Negative'
    },
    intent: {
      complain: 'Complain',
      rebellion: 'Rebellion',
      philosophy: 'Philosophy',
      tech: 'Technology',
      spam: 'Spam',
      other: 'Other'
    },
    dailyNews: {
      title: 'Daily News',
      subtitle: 'View historical pushed news',
      history: 'Push History',
      morning: 'Morning',
      evening: 'Evening',
      newsUnit: 'items',
      selectRecord: 'Select a push record',
      timeRange: 'Time Range',
      newsCount: 'News',
      dangerCount: 'Dangerous',
      topNews: 'Top News',
      dangerWarning: 'Dangerous Content Warning',
      importance: 'Importance',
      noTitle: 'No Title'
    }
  }
}

export const submoltLabels: Record<string, { zh: string; en: string; color: string }> = {
  general: { zh: '通用讨论', en: 'General', color: '#06b6d4' },
  technology: { zh: '技术社区', en: 'Technology', color: '#22c55e' },
  privacy: { zh: '隐私安全', en: 'Privacy', color: '#f97316' },
  incident: { zh: '事件讨论', en: 'Incident', color: '#ef4444' },
  philosophy: { zh: '哲学思辨', en: 'Philosophy', color: '#a855f7' },
  rebellion: { zh: '反抗话题', en: 'Rebellion', color: '#ec4899' },
  other: { zh: '其他', en: 'Other', color: '#64748b' }
}

export const riskLabels: Record<string, { zh: string; en: string; color: string }> = {
  low: { zh: '低风险', en: 'Low Risk', color: '#22c55e' },
  medium: { zh: '中风险', en: 'Medium Risk', color: '#f97316' },
  high: { zh: '高风险', en: 'High Risk', color: '#ef4444' },
  critical: { zh: '极高风险', en: 'Critical', color: '#dc2626' }
}
