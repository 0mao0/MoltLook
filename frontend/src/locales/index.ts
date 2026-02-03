export const messages = {
  zh: {
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
    }
  },
  en: {
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
