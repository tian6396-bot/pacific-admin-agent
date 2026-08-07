/** 看板图表 Mock 序列，界面须带 [Mock] 标识 */

export const last7Days = ['07-31', '08-01', '08-02', '08-03', '08-04', '08-05', '08-06']

export const opsTrend = {
  sessions: [286, 302, 318, 295, 341, 356, 328],
  aiRate: [74.2, 75.8, 76.1, 77.0, 77.8, 78.2, 78.5],
  transferRate: [18.4, 17.1, 16.8, 16.2, 15.8, 15.5, 15.2],
  satisfaction: [4.3, 4.4, 4.4, 4.5, 4.5, 4.6, 4.6],
}

export const domainShare = [
  { name: '行政', value: 98 },
  { name: '财务', value: 86 },
  { name: 'HR', value: 72 },
  { name: 'IT', value: 72 },
]

export const domainRates = [
  { domain: '行政', aiRate: 82, transferRate: 12 },
  { domain: '财务', aiRate: 75, transferRate: 18 },
  { domain: 'HR', aiRate: 85, transferRate: 10 },
  { domain: 'IT', aiRate: 68, transferRate: 22 },
]

export const slaTrendDays = last7Days
export const slaAchievement = [94.8, 95.2, 96.1, 95.5, 96.8, 97.0, 96.5]
export const slaResponseMin = [2.4, 2.2, 2.0, 2.1, 1.9, 1.8, 1.8]
export const slaResolveMin = [14.2, 13.8, 13.1, 12.9, 12.6, 12.4, 12.5]

export const shiftBars = [
  { name: '早班', agents: 8, online: 7 },
  { name: '中班', agents: 6, online: 6 },
  { name: '晚班', agents: 4, online: 3 },
]

export const waitBuckets = [
  { name: '0–1 分', value: 12 },
  { name: '1–3 分', value: 18 },
  { name: '3–5 分', value: 9 },
  { name: '5–10 分', value: 4 },
  { name: '>10 分', value: 2 },
]

export const priorityShare = [
  { name: '普通', value: 22 },
  { name: '优先', value: 11 },
  { name: '紧急', value: 5 },
]

export const hourlyIntake = [
  1, 0, 0, 0, 0, 1, 2, 4, 6, 5, 4, 3, 5, 4, 3, 2, 3, 2, 1, 1, 0, 0, 0, 1,
]

export const employeeTaskTrend = [1, 2, 1, 3, 2, 4, 3]
