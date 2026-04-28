<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
onMounted(() => {
  themeStore.applyTheme()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

/* 亮色主题（默认） */
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f7fa;
  --text-primary: #303133;
  --text-secondary: #606266;
  --text-muted: #909399;
  --border-color: #ebeef5;
  --card-bg: #ffffff;
  --header-bg: #ffffff;
}

/* 深色主题 */
.dark {
  --bg-primary: #1a1a1a;
  --bg-secondary: #141414;
  --text-primary: #e5e5e5;
  --text-secondary: #b0b0b0;
  --text-muted: #707070;
  --border-color: #2d2d2d;
  --card-bg: #1e1e1e;
  --header-bg: #1a1a1a;
}

body.dark {
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* Element Plus 深色模式覆盖 */
.dark .el-card {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

.dark .el-table {
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

.dark .el-table tr {
  background-color: var(--card-bg);
}

.dark .el-table th {
  background-color: var(--bg-secondary);
}

.dark .el-input__wrapper {
  background-color: var(--bg-secondary);
}

.dark .el-textarea__inner {
  background-color: var(--bg-secondary);
}

.dark .el-dialog {
  background-color: var(--card-bg);
}

.dark .el-message-box {
  background-color: var(--card-bg);
}

.dark .el-popover {
  background-color: var(--card-bg);
}

@media (min-width: 768px) {
  .el-dialog {
    width: 90% !important;
    max-width: 600px !important;
  }
}
</style>
