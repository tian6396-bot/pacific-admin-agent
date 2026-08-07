<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { listServices, type ServiceItem } from '@/services/catalogService'

type DomainKey =
  | 'all'
  | 'expense'
  | 'travel'
  | 'hr'
  | 'admin'
  | 'it'
  | 'asset'
  | 'desk'
  | 'material'

const router = useRouter()
const activeDomain = ref<DomainKey>('all')
const keyword = ref('')
const items = ref<ServiceItem[]>([])
const loading = ref(false)
const error = ref('')

const domains: { key: DomainKey; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'expense', label: '费用报销' },
  { key: 'travel', label: '差旅' },
  { key: 'hr', label: 'HR' },
  { key: 'admin', label: '行政办公' },
  { key: 'it', label: 'IT' },
  { key: 'asset', label: '资产采购' },
  { key: 'desk', label: '服务台' },
  { key: 'material', label: '开放材料' },
]

const filtered = computed(() =>
  items.value.filter((it) => {
    const domainOk = activeDomain.value === 'all' || it.domain === activeDomain.value
    const kw = keyword.value.trim()
    const kwOk = !kw || it.name.includes(kw) || it.description.includes(kw)
    return domainOk && kwOk
  }),
)

async function load() {
  loading.value = true
  error.value = ''
  try {
    items.value = await listServices()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function runAction(row: ServiceItem) {
  if (row.action.includes('@')) {
    sessionStorage.setItem('chat_seed', '@转人工')
    router.push('/chat')
    return
  }
  if (row.can_apply) {
    router.push(`/services/${row.id}/apply`)
    return
  }
  sessionStorage.setItem('chat_seed', row.name)
  router.push('/chat')
}

onMounted(load)
</script>

<template>
  <div class="page-shell">
    <aside class="domains">
      <div class="section-label">业务域</div>
      <button
        v-for="d in domains"
        :key="d.key"
        type="button"
        class="domain-item"
        :class="{ active: activeDomain === d.key }"
        @click="activeDomain = d.key"
      >
        {{ d.label }}
      </button>
      <RouterLink to="/workbench" class="back">← 回 Agent 首页</RouterLink>
    </aside>

    <section class="content">
      <header class="head">
        <div>
          <h1>全部服务</h1>
          <p>浏览目录 · 主路径仍建议直接问 Agent；本页不作为第二首页</p>
        </div>
        <input v-model="keyword" class="input search" type="search" placeholder="搜索事项…" />
      </header>

      <div class="notice">
        不确定选哪项？回工作台直接提问，Agent 会路由到对应 Skill / 表单。
      </div>
      <p v-if="error" class="err">{{ error }}</p>
      <p v-if="loading" class="muted">加载中…</p>

      <div class="card table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>事项</th>
              <th>域</th>
              <th>优先级</th>
              <th>说明</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in filtered" :key="row.id" :class="{ highlight: idx === 0 }">
              <td>{{ row.name }}</td>
              <td>{{ row.domain_label }}</td>
              <td>
                <span :class="row.priority === 'P0' ? 'pri-p0' : ''">{{ row.priority }}</span>
              </td>
              <td>{{ row.description }}</td>
              <td>
                <button class="link-btn" type="button" @click="runAction(row)">{{ row.action }}</button>
              </td>
            </tr>
            <tr v-if="!loading && !filtered.length">
              <td colspan="5" class="muted">暂无服务</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-shell {
  display: flex;
  height: calc(100vh - var(--header-h));
  min-height: 0;
}

.domains {
  width: 220px;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.domain-item {
  border: none;
  background: transparent;
  text-align: left;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text);
}

.domain-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 600;
}

.back {
  margin-top: auto;
  text-align: center;
  padding: 9px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
}

.content {
  flex: 1;
  min-width: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.head h1 {
  margin: 0 0 4px;
  font-size: 18px;
}

.head p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.search {
  width: 240px;
  height: 34px;
}

.notice {
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--color-primary-soft);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  font-size: 12px;
}

.table-wrap {
  overflow: auto;
}

.highlight td:first-child {
  color: var(--color-primary);
  font-weight: 600;
}

.pri-p0 {
  color: var(--color-danger);
  font-weight: 600;
}

.link-btn {
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.err {
  color: #cf1322;
  font-size: 13px;
  margin: 0;
}

.muted {
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
