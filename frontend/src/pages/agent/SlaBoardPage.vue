<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { EChartsOption } from 'echarts'
import PageHeader from '@/components/PageHeader.vue'
import BaseChart from '@/components/BaseChart.vue'
import { baseGrid, baseTooltip, chartColors, emptyAxisOption } from '@/utils/chartTheme'
import { getSlaBoard } from '@/services/notifyService'

const loading = ref(false)
const error = ref('')
const kpi = ref({ sla_ok_rate: 100, overdue: 0, avg_wait_minutes: 0, waiting: 0 })
const queues = ref<
  { queue: string; target: string; actual: string; rate: number; status: string }[]
>([])
const shifts = ref<
  { name: string; time: string; agents: number; online: number; sla: number; demo?: boolean }[]
>([])
const trendLabels = ref<string[]>([])
const trendResolved = ref<number[]>([])

const slaKpis = computed(() => [
  { label: 'SLA 达成率', value: kpi.value.sla_ok_rate, unit: '%' },
  { label: '超时工单', value: kpi.value.overdue, unit: '单' },
  { label: '平均等待', value: kpi.value.avg_wait_minutes, unit: '分钟' },
  { label: '排队中', value: kpi.value.waiting, unit: '人' },
])

const trendOption = computed<EChartsOption>(() =>
  emptyAxisOption({
    tooltip: baseTooltip('axis'),
    grid: baseGrid(),
    xAxis: {
      type: 'category',
      data: trendLabels.value,
      axisLabel: { color: chartColors.muted },
    },
    yAxis: {
      type: 'value',
      name: '结案数',
      axisLabel: { color: chartColors.muted },
      splitLine: { lineStyle: { color: chartColors.track, type: 'dashed' } },
    },
    series: [
      {
        name: '已解决工单',
        type: 'line',
        smooth: true,
        data: trendResolved.value,
        lineStyle: { width: 2.5, color: chartColors.primary },
        itemStyle: { color: chartColors.primary },
      },
    ],
  }),
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const board = await getSlaBoard()
    kpi.value = board.kpi
    queues.value = board.queues
    shifts.value = board.shifts
    trendLabels.value = board.trend_labels
    trendResolved.value = board.trend_resolved
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="SLA 与班次看板" description="真实队列 KPI + 演示排班" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="muted">加载中…</p>

    <div class="stats card">
      <div v-for="item in slaKpis" :key="item.label" class="stat-item">
        <span class="stat-value">{{ item.value }}<small>{{ item.unit }}</small></span>
        <span class="stat-label">{{ item.label }}</span>
      </div>
    </div>

    <div class="card chart-card">
      <h3>近 7 日结案趋势</h3>
      <BaseChart :option="trendOption" height="260px" />
    </div>

    <div class="grid-2">
      <div class="card section">
        <h3>班次安排 <small class="hint">演示排班</small></h3>
        <table class="table">
          <thead>
            <tr>
              <th>班次</th>
              <th>时段</th>
              <th>编制</th>
              <th>在线</th>
              <th>SLA</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in shifts" :key="s.name">
              <td>{{ s.name }}</td>
              <td>{{ s.time }}</td>
              <td>{{ s.agents }} 人</td>
              <td>{{ s.online }} 人</td>
              <td>{{ s.sla }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card section">
        <h3>队列 SLA 配置</h3>
        <table class="table">
          <thead>
            <tr>
              <th>队列</th>
              <th>目标</th>
              <th>参考实际</th>
              <th>达成率</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="q in queues" :key="q.queue">
              <td>{{ q.queue }}</td>
              <td>{{ q.target }}</td>
              <td>{{ q.actual }}</td>
              <td>{{ q.rate }}%</td>
              <td>
                <span class="tag" :class="q.status === 'ok' ? 'tag-success' : 'tag-primary'">
                  {{ q.status === 'ok' ? '正常' : '关注' }}
                </span>
              </td>
            </tr>
            <tr v-if="!queues.length">
              <td colspan="5" class="muted">暂无队列配置</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
  margin-bottom: 16px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-value {
  font-size: 22px;
  font-weight: 600;
}
.stat-value small {
  font-size: 12px;
  margin-left: 4px;
  font-weight: 400;
  color: var(--color-text-secondary);
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.chart-card {
  padding: 16px;
  margin-bottom: 16px;
}
.chart-card h3,
.section h3 {
  margin: 0 0 12px;
  font-size: 14px;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.section {
  padding: 16px;
  overflow-x: auto;
}
.hint {
  font-weight: 400;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.err {
  color: #cf1322;
}
.muted {
  color: var(--color-text-secondary);
  text-align: center;
  padding: 12px;
}
@media (max-width: 900px) {
  .stats,
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>
