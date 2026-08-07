<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PageHeader from '@/components/PageHeader.vue'
import {
  listIntents,
  offlineIntent,
  publishIntent,
  updateIntent,
  type ConfigStatus,
  type IntentItem,
} from '@/services/opsService'

const intents = ref<IntentItem[]>([])
const selectedId = ref('')
const drawerOpen = ref(true)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const editing = ref(false)
const draftPrompt = ref('')

const statusMap: Record<ConfigStatus, { label: string; tag: string }> = {
  published: { label: '已发布', tag: 'tag-success' },
  draft: { label: '草稿', tag: 'tag-muted' },
  offline: { label: '已下线', tag: 'tag-danger' },
}

const activeIntent = computed(() => intents.value.find((i) => i.id === selectedId.value))

async function load() {
  loading.value = true
  error.value = ''
  try {
    intents.value = await listIntents()
    if (!selectedId.value && intents.value.length) {
      selectedId.value = intents.value[0].id
    }
    syncDraft()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function selectIntent(id: string) {
  selectedId.value = id
  drawerOpen.value = true
  editing.value = false
  syncDraft()
}

function syncDraft() {
  draftPrompt.value = activeIntent.value?.prompt_content || ''
}

async function savePrompt() {
  if (!activeIntent.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await updateIntent(activeIntent.value.id, {
      prompt_content: draftPrompt.value,
    })
    const idx = intents.value.findIndex((i) => i.id === updated.id)
    if (idx >= 0) intents.value[idx] = updated
    editing.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    saving.value = false
  }
}

async function doPublish() {
  if (!activeIntent.value) return
  saving.value = true
  error.value = ''
  try {
    if (editing.value) {
      await updateIntent(activeIntent.value.id, { prompt_content: draftPrompt.value })
    }
    const updated = await publishIntent(activeIntent.value.id)
    const idx = intents.value.findIndex((i) => i.id === updated.id)
    if (idx >= 0) intents.value[idx] = updated
    editing.value = false
    syncDraft()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '发布失败'
  } finally {
    saving.value = false
  }
}

async function doOffline() {
  if (!activeIntent.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await offlineIntent(activeIntent.value.id)
    const idx = intents.value.findIndex((i) => i.id === updated.id)
    if (idx >= 0) intents.value[idx] = updated
  } catch (e) {
    error.value = e instanceof Error ? e.message : '下线失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <PageHeader title="意图与 Prompt 管理" description="意图配置与 Prompt 版本管理" icon="◆" />

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="layout">
      <div class="card table-wrap main-table">
        <table class="table">
          <thead>
            <tr>
              <th>意图 ID</th>
              <th>名称</th>
              <th>领域</th>
              <th>槽位</th>
              <th>Prompt 版本</th>
              <th>命中率</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="intent in intents"
              :key="intent.id"
              :class="{ active: selectedId === intent.id }"
              @click="selectIntent(intent.id)"
            >
              <td class="mono">{{ intent.id }}</td>
              <td>{{ intent.name }}</td>
              <td>{{ intent.domain }}</td>
              <td>{{ intent.slots }}</td>
              <td>{{ intent.prompt_version }}</td>
              <td>{{ intent.hit_rate > 0 ? `${intent.hit_rate}%` : '—' }}</td>
              <td>
                <span class="tag" :class="statusMap[intent.status].tag">
                  {{ statusMap[intent.status].label }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <aside v-if="drawerOpen && activeIntent" class="card drawer">
        <div class="drawer-head">
          <span>{{ activeIntent.name }} · Prompt</span>
          <button type="button" class="link" @click="drawerOpen = false">收起</button>
        </div>
        <div class="drawer-body">
          <div class="prompt-version">
            <div class="pv-head">
              <span class="tag tag-primary">{{ activeIntent.prompt_version }}</span>
              <span class="pv-meta">当前配置</span>
            </div>
            <textarea
              v-if="editing"
              v-model="draftPrompt"
              class="prompt-edit"
              rows="12"
            />
            <pre v-else class="prompt-content">{{ activeIntent.prompt_content || '（空）' }}</pre>
            <div class="pv-actions">
              <button
                v-if="!editing"
                type="button"
                class="btn btn-ghost"
                :disabled="saving"
                @click="editing = true; syncDraft()"
              >
                编辑
              </button>
              <button
                v-else
                type="button"
                class="btn btn-ghost"
                :disabled="saving"
                @click="savePrompt"
              >
                保存
              </button>
              <button type="button" class="btn btn-primary" :disabled="saving" @click="doPublish">
                发布
              </button>
              <button
                v-if="activeIntent.status === 'published'"
                type="button"
                class="btn btn-ghost"
                :disabled="saving"
                @click="doOffline"
              >
                下线
              </button>
            </div>
          </div>
        </div>
      </aside>
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
.layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
}
.main-table {
  overflow-x: auto;
}
.main-table tbody tr {
  cursor: pointer;
}
.drawer {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - var(--header-h) - 120px);
}
.drawer-head {
  flex-shrink: 0;
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.prompt-version {
  margin-bottom: 16px;
}
.pv-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.pv-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.prompt-content,
.prompt-edit {
  margin: 0;
  padding: 12px;
  background: var(--color-bg);
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  font-family: ui-monospace, Consolas, monospace;
  width: 100%;
  box-sizing: border-box;
  border: 1px solid var(--color-border);
}
.pv-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>
