import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
  { path: '/api-one-click', name: 'api-one-click', component: () => import('@/views/ApiOneClick.vue'), meta: { title: '一键接入API' } },
  { path: '/screenshot', name: 'screenshot', component: () => import('@/views/Screenshot.vue'), meta: { title: '长截图' } },
  { path: '/ocr', name: 'ocr', component: () => import('@/views/Ocr.vue'), meta: { title: '截图识字' } },
  { path: '/dev', name: 'dev', component: () => import('@/views/Dev.vue'), meta: { title: '开发工具箱' } },
  { path: '/ops', name: 'ops', component: () => import('@/views/Ops.vue'), meta: { title: '运营工具箱' } },
  { path: '/more', name: 'more', component: () => import('@/views/More.vue'), meta: { title: '更多工具' } },
  { path: '/ai-skills', name: 'ai-skills', component: () => import('@/views/AiSkills.vue'), meta: { title: 'AI-Skills' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
