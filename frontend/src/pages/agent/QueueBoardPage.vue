<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { EChartsOption } from 'echarts'
import PageHeader from '@/components/PageHeader.vue'
import BaseChart from '@/components/BaseChart.vue'
import { baseGrid, baseTooltip, chartColors, emptyAxisOption } from '@/utils/chartTheme'
import {
  claimTicket,
  connectTicketSocket,
  getQueueBoard,
  priorityMap,
  type TicketItem,
} from '@/services/ticketService'

const router = useRouter()
const items = ref<TicketItem[]>([])
const kpi = ref({ waiting: 0, today_claimed: 0, avg_wait_minutes: 0, sla_ok_rate: 100 })
const loading = ref(false)
const error = ref('')
const claiming = ref('')
let ws: WebSocket | null = null

const kpis = computed(() => [
  { label: '排队中', value: kpi.value.waiting, unit: '人' },
  { label: '今日接入', value: kpi.value.today_claimed, unit: '次' },
  { label: '平均等待', value: kpi.value.avg_wait_minutes, unit: '分钟' },
  { label: 'SLA 达成率', value: kpi.value.sla_ok_rate, unit: '%' },
])

function slaLabel(item: TicketItem) {
  if (item.sla_overdue) return '已超时'
  if (!item.sla_deadline) return '—'
  const remain = Math.max(
    0,
    Math.round((new Date(item.sla_deadline).getTime() - Date.now()) / 60000),
  )
  return `${remain} 分钟`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const board = await getQueueBoard()
    kpi.value = board.kpi
    items.value = board.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function onClaim(item: TicketItem) {
  if (item.status !== 'waiting') {
    router.push(`/agent/sessions/${item.id}`)
    return
  }
  claiming.value = item.id
  try {
    await claimTicket(item.id)
    router.push(`/agent/sessions/${item.id}`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '接管失败'
  } finally {
    claiming.value = ''
  }
}

const waitBuckets = computed(() => {
  const buckets = [
    { name: '0-1分', value: 0 },
    { name: '1-3分', value: 0 },
    { name: '3-5分', value: 0 },
    { name: '5分+', value: 0 },
  ]
  for (const it of items.value.filter((x) => x.status === 'waiting')) {
    const m = it.wait_minutes
    if (m <= 1) buckets[0].value++
    else if (m <= 3) buckets[1].value++
    else if (m <= 5) buckets[2].value++
    else buckets[3].value++
  }
  return buckets
})

const priorityShare = computed(() => {
  const map = { normal: 0, high: 0, urgent: 0 }
  for (const it of items.value) {
    map[it.priority]++
  }
  return [
    { name: '普通', value: map.normal },
    { name: '优先', value: map.high },
    { name: '紧急', value: map.urgent },
  ]
})

const waitOption = computed<EChartsOption>(() =>
  emptyAxisOption({
    tooltip: baseTooltip('axis'),
    grid: baseGrid({ top: 28 }),
    xAxis: {
      type: 'category',
      data: waitBuckets.value.map((b) => b.name),
      axisLine: { lineStyle: { color: chartColors.track } },
      axisLabel: { color: chartColors.muted, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '会话数',
      minInterval: 1,
      splitLine: { lineStyle: { color: chartColors.track, type: 'dashed' } },
      axisLabel: { color: chartColors.muted },
    },
    series: [
      {
        name: '等待时长',
        type: 'bar',
        barMaxWidth: 36,
        data: waitBuckets.value.map((b, i) => ({
          value: b.value,
          itemStyle: {
            color: i >= 3 ? chartColors.danger : i === 2 ? chartColors.warning : chartColors.primary,
            borderRadius: [4, 4, 0, 0],
          },
        })),
      },
    ],
  }),
)

const priorityOption = computed<EChartsOption>(() =>
  emptyAxisOption({
    tooltip: baseTooltip('item'),
    legend: { bottom: 0, textStyle: { color: chartColors.muted } },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        data: priorityShare.value.map((p, i) => ({
          ...p,
          itemStyle: {
            color: [chartColors.track, chartColors.primary, chartColors.danger][i],
          },
        })),
      },
    ],
  }),
)

onMounted(() => {
  load()
  ws = connectTicketSocket('agent:queue', {
    onEvent: (data) => {
      if (data.type === 'queue') load()
    },
  })
})

onUnmounted(() => {
  ws?.close()
})
</script>

<template>
  <div class="page">
    <PageHeader title="队列看板" description="实时排队会话与 SLA 预警" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>

    <div class="stats card">
      <div v-for="item in kpis" :key="item.label" class="stat-item">
        <span class="stat-value">{{ item.value }}<small>{{ item.unit }}</small></span>
        <span class="stat-label">{{ item.label }}</span>
      </div>
    </div>

    <div class="charts-grid">
      <div class="card chart-card">
        <h3>等待时长分布</h3>
        <BaseChart :option="waitOption" height="260px" />
      </div>
      <div class="card chart-card">
        <h3>优先级占比</h3>
        <BaseChart :option="priorityOption" height="260px" />
      </div>
    </div>

    <div class="card table-wrap">
      <p v-if="loading" class="muted">加载中…</p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>工单</th>
            <th>员工</th>
            <th>部门</th>
            <th>咨询主题</th>
            <th>来源</th>
            <th>等待</th>
            <th>优先级</th>
            <th>SLA</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" :class="{ overdue: item.sla_overdue }">
            <td class="mono">{{ item.id.slice(0, 8) }}</td>
            <td>{{ item.employee_name }}</td>
            <td>{{ item.employee_dept || '—' }}</td>
            <td>{{ item.subject }}</td>
            <td>{{ item.channel }}</td>
            <td>{{ item.wait_minutes }} 分钟</td>
            <td>
              <span class="tag" :class="priorityMap[item.priority].tag">
                {{ priorityMap[item.priority].label }}
              </span>
            </td>
            <td>
              <span :class="{ 'sla-overdue': item.sla_overdue }">{{ slaLabel(item) }}</span>
            </td>
            <td>{{ item.status }}</td>
            <td>
              <button
                class="btn btn-primary btn-sm"
                type="button"
                :disabled="claiming === item.id"
                @click="onClaim(item)"
              >
                {{ item.status === 'waiting' ? '接入' : '进入' }}
              </button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td colspan="10" class="muted">当前无排队/在办工单</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.err {
  color: #cf1322;
  margin-bottom: 8px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  padding: 0;
  margin-bottom: 16px;
  overflow: hidden;
}
.stat-item {
  padding: 20px 24px;
  text-align: center;
  background: var(--color-surface);
}
.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
}
.stat-value small {
  font-size: 12px;
  margin-left: 4px;
  font-weight: 500;
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 16px;
}
.chart-card {
  padding: 14px;
}
.chart-card h3 {
  margin: 0 0 8px;
  font-size: 13px;
}
.sla-overdue,
.overdue td {
  color: var(--color-danger);
  font-weight: 600;
}
.muted {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 16px;
}
.btn-sm {
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
}
@media (max-width: 900px) {
  .stats,
  .charts-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
