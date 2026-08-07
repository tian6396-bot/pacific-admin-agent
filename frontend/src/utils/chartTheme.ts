import type { EChartsOption } from 'echarts'

export const chartColors = {
  primary: '#1677ff',
  secondary: '#69b1ff',
  success: '#52c41a',
  warning: '#fa8c16',
  danger: '#ff4d4f',
  muted: '#8c8c8c',
  track: '#f0f2f5',
  text: '#1f1f1f',
  palette: ['#1677ff', '#52c41a', '#fa8c16', '#722ed1', '#13c2c2', '#eb2f96'],
}

export function baseGrid(extra?: Record<string, unknown>) {
  return {
    left: 40,
    right: 16,
    top: 36,
    bottom: 28,
    containLabel: true,
    ...extra,
  }
}

export function baseTooltip(trigger: 'axis' | 'item' = 'axis') {
  return {
    trigger,
    backgroundColor: '#ffffff',
    borderColor: '#e8e8e8',
    textStyle: { color: chartColors.text, fontSize: 12 },
  }
}

export function emptyAxisOption(partial: EChartsOption): EChartsOption {
  return {
    color: chartColors.palette,
    textStyle: { color: chartColors.muted, fontFamily: 'Noto Sans SC, sans-serif' },
    ...partial,
  }
}
