<script setup lang="ts">
import { ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import MockBadge from '@/components/MockBadge.vue'

const domains = ['行政', 'HR', '财务', 'IT'] as const
type Domain = (typeof domains)[number]

const selectedDomain = ref<Domain>('财务')
const expert = ref('')
const reason = ref('员工出差机票超标 380 元，需财务确认超标审批流程及报销科目。')
const urgency = ref('normal')
const relatedTicket = ref('TK-1001')
const relatedSession = ref('s-001')

const experts: Record<Domain, string[]> = {
  行政: ['行政专员 · 小刘', '行政主管 · 陈经理'],
  HR: ['HR 专员 · 王芳', 'HRBP · 赵总'],
  财务: ['财务专员 · 周会计', '财务主管 · 吴经理'],
  IT: ['IT 运维 · 张工', 'IT 主管 · 孙经理'],
}
</script>

<template>
  <div class="page">
    <PageHeader title="协同专家" description="转派至行政 / HR / 财务 / IT 专家处理" icon="◆">
      <template #badge><MockBadge /></template>
    </PageHeader>

    <div class="card form-card">
      <div class="field">
        <span class="label">协同领域</span>
        <div class="domain-tabs">
          <button
            v-for="d in domains"
            :key="d"
            type="button"
            class="filter-chip"
            :class="{ active: selectedDomain === d }"
            @click="selectedDomain = d"
          >
            {{ d }}
          </button>
        </div>
      </div>

      <div class="field">
        <label class="label" for="expert">选择专家</label>
        <select id="expert" v-model="expert" class="input">
          <option value="">请选择专家</option>
          <option v-for="e in experts[selectedDomain]" :key="e" :value="e">{{ e }}</option>
        </select>
      </div>

      <div class="field">
        <label class="label" for="reason">转派说明</label>
        <textarea id="reason" v-model="reason" class="textarea" rows="4" />
      </div>

      <div class="field-row">
        <div class="field">
          <label class="label" for="ticket">关联工单</label>
          <input id="ticket" v-model="relatedTicket" class="input mono" />
        </div>
        <div class="field">
          <label class="label" for="session">关联会话</label>
          <input id="session" v-model="relatedSession" class="input mono" />
        </div>
      </div>

      <div class="field">
        <span class="label">紧急程度</span>
        <div class="urgency-group">
          <label><input v-model="urgency" type="radio" value="normal" /> 普通</label>
          <label><input v-model="urgency" type="radio" value="high" /> 优先</label>
          <label><input v-model="urgency" type="radio" value="urgent" /> 紧急</label>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn btn-ghost">取消</button>
        <button type="button" class="btn btn-primary">提交转派</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-card {
  max-width: 640px;
  padding: 24px;
}

.domain-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.urgency-group {
  display: flex;
  gap: 20px;
  font-size: 13px;
}

.urgency-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}
</style>
