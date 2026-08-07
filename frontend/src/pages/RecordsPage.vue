<script setup lang="ts">
import PageHeader from '@/components/PageHeader.vue'
import MockBadge from '@/components/MockBadge.vue'

interface Record {
  id: string
  title: string
  type: string
  status: 'done' | 'rejected' | 'cancelled'
  result: string
  finishedAt: string
}

const records: Record[] = [
  { id: 'R-20260301001', title: 'IT 报修 · 笔记本 Wi-Fi', type: 'IT', status: 'done', result: '已修复，网络正常', finishedAt: '2026-03-01 14:00' },
  { id: 'R-20260228002', title: 'VPN 权限开通', type: 'IT', status: 'done', result: '权限已开通，有效期 90 天', finishedAt: '2026-02-28 11:30' },
  { id: 'R-20260215003', title: '访客预约 · 张总来访', type: '行政', status: 'done', result: '访客已登记，门禁已授权', finishedAt: '2026-02-15 09:00' },
  { id: 'R-20260210004', title: '发票开具 · 技术服务费', type: '财务', status: 'rejected', result: '驳回：缺少合同附件', finishedAt: '2026-02-10 16:45' },
  { id: 'R-20260120005', title: '用印申请 · 保密协议', type: '行政', status: 'cancelled', result: '申请人主动撤回', finishedAt: '2026-01-20 10:20' },
]

const statusMap = {
  done: { label: '已完成', tag: 'tag-success' },
  rejected: { label: '已驳回', tag: 'tag-danger' },
  cancelled: { label: '已撤回', tag: 'tag-muted' },
} as const
</script>

<template>
  <div class="page">
    <PageHeader title="办理记录" description="历史申请单号、状态与办理结果" icon="◆">
      <template #badge><MockBadge /></template>
    </PageHeader>

    <div class="card table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>单号</th>
            <th>标题</th>
            <th>类型</th>
            <th>状态</th>
            <th>办理结果</th>
            <th>完成时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rec in records" :key="rec.id">
            <td class="mono">{{ rec.id }}</td>
            <td>{{ rec.title }}</td>
            <td>{{ rec.type }}</td>
            <td>
              <span class="tag" :class="statusMap[rec.status].tag">
                {{ statusMap[rec.status].label }}
              </span>
            </td>
            <td>{{ rec.result }}</td>
            <td>{{ rec.finishedAt }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-wrap {
  overflow-x: auto;
}
</style>
