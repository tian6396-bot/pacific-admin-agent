import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/EmployeeLayout.vue'),
    meta: { requiresAuth: true, roles: ['employee'] satisfies UserRole[] },
    children: [
      { path: '', redirect: '/workbench' },
      { path: 'workbench', name: 'workbench', component: () => import('@/pages/WorkbenchPage.vue') },
      { path: 'chat', name: 'chat', component: () => import('@/pages/ChatPage.vue') },
      { path: 'services', name: 'services', component: () => import('@/pages/ServiceHallPage.vue') },
      {
        path: 'services/:id/apply',
        name: 'service-apply',
        component: () => import('@/pages/ServiceApplyPage.vue'),
      },
      { path: 'tasks', name: 'tasks', component: () => import('@/pages/TasksPage.vue') },
      { path: 'tasks/:id', name: 'task-detail', component: () => import('@/pages/TaskDetailPage.vue') },
      { path: 'records', redirect: { path: '/tasks', query: { tab: 'history' } } },
      { path: 'tickets', name: 'tickets', component: () => import('@/pages/TicketsPage.vue') },
      { path: 'materials', name: 'materials', component: () => import('@/pages/MaterialsPage.vue') },
      { path: 'messages', name: 'messages', component: () => import('@/pages/MessagesPage.vue') },
      { path: 'settings', name: 'settings', component: () => import('@/pages/SettingsPage.vue') },
    ],
  },
  {
    path: '/agent',
    component: () => import('@/layouts/AgentLayout.vue'),
    meta: { requiresAuth: true, roles: ['agent'] satisfies UserRole[] },
    children: [
      { path: '', redirect: '/agent/queue' },
      { path: 'queue', name: 'agent-queue', component: () => import('@/pages/agent/QueueBoardPage.vue') },
      {
        path: 'sessions/:id?',
        name: 'agent-session',
        component: () => import('@/pages/agent/SessionWorkbenchPage.vue'),
      },
      {
        // 旧 Mock 工单页易误导；统一到真实队列/会话
        path: 'tickets/:id?',
        redirect: (to) =>
          to.params.id
            ? { path: `/agent/sessions/${to.params.id}` }
            : { path: '/agent/queue' },
      },
      { path: 'collab', redirect: '/agent/queue' },
      { path: 'sla', name: 'agent-sla', component: () => import('@/pages/agent/SlaBoardPage.vue') },
      { path: 'qa', name: 'agent-qa', component: () => import('@/pages/agent/QaFollowupPage.vue') },
      {
        path: 'tasks',
        name: 'agent-tasks',
        component: () => import('@/pages/TasksPage.vue'),
      },
      {
        path: 'tasks/:id',
        name: 'agent-task-detail',
        component: () => import('@/pages/TaskDetailPage.vue'),
      },
    ],
  },

  {
    path: '/ops',
    component: () => import('@/layouts/OpsLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'] satisfies UserRole[] },
    children: [
      { path: '', redirect: '/ops/knowledge' },
      {
        path: 'knowledge',
        name: 'ops-knowledge',
        component: () => import('@/pages/ops/KnowledgePage.vue'),
      },
      {
        path: 'knowledge/:id/parse',
        name: 'ops-knowledge-parse',
        component: () => import('@/pages/ops/KnowledgeParsePage.vue'),
      },
      { path: 'catalog', name: 'ops-catalog', component: () => import('@/pages/ops/CatalogPage.vue') },
      { path: 'intents', name: 'ops-intents', component: () => import('@/pages/ops/IntentsPage.vue') },
      {
        path: 'skills',
        name: 'ops-skills',
        component: () => import('@/pages/ops/WorkflowsPage.vue'),
      },
      { path: 'workflows', redirect: '/ops/skills' },
      { path: 'tools', name: 'ops-tools', component: () => import('@/pages/ops/ToolsPage.vue') },
      { path: 'queues', name: 'ops-queues', component: () => import('@/pages/ops/QueuesPage.vue') },
      {
        path: 'insights',
        name: 'ops-insights',
        component: () => import('@/pages/ops/InsightsPage.vue'),
      },
      { path: 'badcases', redirect: { path: '/ops/insights' } },
      { path: 'metrics', redirect: { path: '/ops/insights' } },
      {
        path: 'security',
        name: 'ops-security',
        component: () => import('@/pages/ops/SecurityPage.vue'),
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.isAuthenticated && auth.user) {
      if (auth.user.role === 'agent') return '/agent/queue'
      if (auth.user.role === 'admin') return '/ops/knowledge'
      return '/workbench'
    }
    return true
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }

  const roles = to.matched.find((r) => r.meta.roles)?.meta.roles as UserRole[] | undefined
  if (roles && auth.user && !roles.includes(auth.user.role)) {
    if (auth.user.role === 'agent') return '/agent/queue'
    if (auth.user.role === 'admin') return '/ops/knowledge'
    return '/workbench'
  }

  return true
})

export default router
