<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import PageHeader from '@/components/PageHeader.vue'
import BaseChart from '@/components/BaseChart.vue'
import { baseGrid, baseTooltip, chartColors, emptyAxisOption } from '@/utils/chartTheme'
import { getMetrics, type MetricsSummary } from '@/services/opsService'

const props = defineProps<{ embedded?: boolean }>()

const summary = ref<MetricsSummary | null>(null)
const loading = ref(false)
const error = ref('')

const kpis = computed(() => {
  const s = summary.value
  if (!s) return []
  return [
    { label: '今日会话量', value: s.sessions_today, unit: '次' },
    { label: 'AI 解决率', value: s.ai_resolve_rate, unit: '%' },
    { label: '转人工率', value: s.handoff_rate, unit: '%' },
    { label: '平均满意度', value: s.avg_satisfaction, unit: '/5' },
    { label: '已发布知识', value: s.knowledge_published, unit: '篇' },
    { label: '进行中任务', value: s.tasks_open, unit: '单' },
    { label: '排队工单', value: s.tickets_waiting, unit: '单' },
    { label: '待处理 Bad Case', value: s.badcases_open, unit: '条' },
  ]
})

const trendOption = computed<EChartsOption>(() => {
  const s = summary.value
  return emptyAxisOption({
    tooltip: baseTooltip('axis'),
    grid: baseGrid(),
    legend: { show: false },
    xAxis: {
      type: 'category',
      data: s?.trend_labels || [],
      axisLine: { lineStyle: { color: chartColors.track } },
      axisLabel: { color: chartColors.muted },
    },
    yAxis: {
      type: 'value',
      name: '次',
      splitLine: { lineStyle: { color: chartColors.track, type: 'dashed' } },
      axisLabel: { color: chartColors.muted },
    },
    series: [
      {
        name: '会话量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: s?.trend_sessions || [],
        lineStyle: { width: 2.5, color: chartColors.primary },
        itemStyle: { color: chartColors.primary },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(22,119,255,0.22)' },
              { offset: 1, color: 'rgba(22,119,255,0.02)' },
            ],
          },
        },
      },
    ],
  })
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    summary.value = await getMetrics()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page" :class="{ embedded: props.embedded }">
    <PageHeader
      v-if="!props.embedded"
      title="运营看板"
      description="核心指标、趋势与领域分布"
      icon="◆"
    />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="kpi-grid">
      <div v-for="kpi in kpis" :key="kpi.label" class="card kpi-card">
        <span class="kpi-label">{{ kpi.label }}</span>
        <span class="kpi-value">{{ kpi.value }}<small>{{ kpi.unit }}</small></span>
      </div>
    </div>

    <div class="card chart-card">
      <div class="chart-head">近 7 日会话量</div>
      <BaseChart :option="trendOption" height="280px" />
    </div>
  </div>
</template>

<style scoped>
.err {
  color: var(--color-danger, #cf1322);
  font-size: 13px;
  margin: 0 0 12px;
}
.hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 12px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.kpi-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.kpi-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.kpi-value {
  font-size: 22px;
  font-weight: 600;
}
.kpi-value small {
  font-size: 12px;
  font-weight: 400;
  margin-left: 4px;
  color: var(--color-text-secondary);
}
.chart-card {
  padding: 16px;
}
.chart-head {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
}
@media (max-width: 1100px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
