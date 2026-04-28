<template>
  <router-view />
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

onMounted(() => {
  themeStore.applyTheme()
})

watch(() => themeStore.isDark, () => {
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

/* Element Plus 亮色主题 */
:root {
  --el-color-primary: #409eff;
  --el-bg-color: #ffffff;
  --el-bg-color-page: #f0f2f5;
  --el-text-color-primary: #303133;
  --el-text-color-regular: #606266;
  --el-text-color-secondary: #909399;
  --el-text-color-placeholder: #c0c4cc;
  --el-border-color: #dcdfe6;
  --el-border-color-light: #e4e7ed;
  --el-border-color-lighter: #ebeef5;
  --el-fill-color-blank: #ffffff;
}

/* Element Plus 深色主题 */
.dark {
  --el-color-primary: #409eff;
  --el-bg-color: #1e1e1e;
  --el-bg-color-page: #141414;
  --el-bg-color-overlay: #1e1e1e;
  --el-text-color-primary: #e5e5e5;
  --el-text-color-regular: #b0b0b0;
  --el-text-color-secondary: #707070;
  --el-text-color-placeholder: #505050;
  --el-border-color: #2d2d2d;
  --el-border-color-light: #363636;
  --el-border-color-lighter: #404040;
  --el-fill-color-blank: #1e1e1e;
  --el-fill-color: #1a1a1a;
  --el-fill-color-light: #242424;
  --el-fill-color-lighter: #2a2a2a;
  --el-fill-color-dark: #141414;
  --el-fill-color-darker: #101010;
  --el-mask-color: rgba(0, 0, 0, 0.7);

  /* 视图通用颜色变量 */
  --view-bg: #1e1e1e;
  --view-bg-secondary: #242424;
  --view-text-primary: #e5e5e5;
  --view-text-regular: #b0b0b0;
  --view-text-secondary: #707070;
  --view-border: #2d2d2d;
}

/* 全局深色模式覆盖 */
.dark body {
  background: #141414;
  color: #e5e5e5;
}

.dark #app {
  background: #141414;
}

/* Element Plus 组件深色模式 */
.dark .el-card {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

.dark .el-table {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

.dark .el-table el-table__header th {
  background-color: #1a1a1a !important;
}

.dark .el-table el-table__body tr {
  background-color: #1e1e1e;
}

.dark .el-table el-table__body tr:hover > td {
  background-color: #242424;
}

.dark .el-table th.el-table__cell {
  background-color: #1a1a1a;
  color: #e5e5e5;
  border-color: #2d2d2d;
}

.dark .el-table td.el-table__cell {
  border-color: #2d2d2d;
}

.dark .el-pagination {
  background-color: transparent;
}

.dark .el-dialog {
  background-color: #1e1e1e;
  color: #e5e5e5;
}

.dark .el-dialog__header {
  border-bottom: 1px solid #2d2d2d;
}

.dark .el-dialog__title {
  color: #e5e5e5;
}

.dark .el-dropdown-menu {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
}

.dark .el-dropdown-menu__item {
  color: #e5e5e5;
}

.dark .el-dropdown-menu__item:hover {
  background-color: #242424;
}

.dark .el-input__wrapper {
  background-color: #242424;
  box-shadow: 0 0 0 1px #363636 inset;
}

.dark .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #409eff inset;
}

.dark .el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px #409eff inset;
}

.dark .el-input__inner {
  color: #e5e5e5;
}

.dark .el-input__inner::placeholder {
  color: #505050;
}

.dark .el-textarea__inner {
  background-color: #242424;
  color: #e5e5e5;
  box-shadow: 0 0 0 1px #363636 inset;
}

.dark .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #409eff inset;
}

.dark .el-textarea__inner:focus {
  box-shadow: 0 0 0 1px #409eff inset;
}

.dark .el-select__wrapper {
  background-color: #242424;
  box-shadow: 0 0 0 1px #363636 inset;
}

.dark .el-form-item__label {
  color: #b0b0b0;
}

.dark .el-button--default {
  background-color: #242424;
  border-color: #363636;
  color: #e5e5e5;
}

.dark .el-button--default:hover {
  background-color: #2a2a2a;
  border-color: #409eff;
  color: #409eff;
}

.dark .el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
  color: #ffffff;
}

.dark .el-button--primary:hover {
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.dark .el-message {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
  color: #e5e5e5;
}

.dark .el-message-box {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
}

.dark .el-message-box__title {
  color: #e5e5e5;
}

.dark .el-message-box__content {
  color: #b0b0b0;
}

.dark .el-popover {
  background-color: #1e1e1e;
  border-color: #2d2d2d;
}

.dark .el-tag {
  background-color: #242424;
  border-color: #363636;
  color: #e5e5e5;
}

.dark .el-tag--success {
  background-color: rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.3);
  color: #409eff;
}

.dark .el-tag--warning {
  background-color: rgba(230, 162, 60, 0.15);
  border-color: rgba(230, 162, 60, 0.3);
  color: #e6a23c;
}

.dark .el-tag--danger {
  background-color: rgba(245, 108, 108, 0.15);
  border-color: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.dark .el-tag--info {
  background-color: rgba(144, 147, 153, 0.15);
  border-color: rgba(144, 147, 153, 0.3);
  color: #909399;
}

.dark .el-switch.is-checked .el-switch__core {
  background-color: #409eff;
}

.dark .el-slider__runway {
  background-color: #363636;
}

.dark .el-slider__bar {
  background-color: #409eff;
}

.dark .el-checkbox__input.is-checked .el-checkbox__inner {
  background-color: #409eff;
  border-color: #409eff;
}

.dark .el-checkbox__label {
  color: #e5e5e5;
}

.dark .el-radio__input.is-checked .el-radio__inner {
  background-color: #409eff;
  border-color: #409eff;
}

.dark .el-radio__label {
  color: #e5e5e5;
}

.dark .el-tabs__item {
  color: #707070;
}

.dark .el-tabs__item.is-active {
  color: #409eff;
}

.dark .el-tabs__active-bar {
  background-color: #409eff;
}

.dark .el-tabs__nav-wrap::after {
  background-color: #2d2d2d;
}

.dark .el-menu {
  background-color: transparent;
  border-color: #2d2d2d;
}

.dark .el-menu--horizontal {
  background-color: transparent;
}

.dark .el-menu-item {
  color: #b0b0b0;
}

.dark .el-menu-item:hover {
  background-color: #242424;
}

.dark .el-menu-item.is-active {
  color: #409eff;
}

.dark .el-aside {
  background-color: #1a1a1a;
}

.dark .el-header {
  background-color: #1a1a1a;
  border-color: #2d2d2d;
}

.dark .el-main {
  background-color: #141414;
}

.dark .el-empty__description {
  color: #707070;
}

.dark .el-segmented {
  background-color: #242424;
}

.dark .el-segmented__item {
  color: #b0b0b0;
}

.dark .el-segmented__item.is-selected {
  background-color: #1e1e1e;
  color: #409eff;
}

@media (min-width: 768px) {
  .el-dialog {
    width: 90% !important;
    max-width: 600px !important;
  }
}

/* ===== 视图通用深色模式覆盖 ===== */
.dark .chat-container,
.dark .knowledge-container,
.dark .memory-container,
.dark .history-container,
.dark .billing-container,
.dark .profile-container {
  background: var(--view-bg) !important;
}

/* Chat 视图 */
.dark .chat-header {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .chat-input {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .main-header {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .page-title {
  color: var(--view-text-primary) !important;
}

.dark .token-badge {
  background: var(--view-bg-secondary) !important;
  color: var(--view-text-regular) !important;
}

.dark .empty-state {
  color: var(--view-text-secondary) !important;
}

.dark .sender {
  color: var(--view-text-regular) !important;
}

.dark .time {
  color: var(--view-text-secondary) !important;
}

.dark .message-item.assistant .message-text {
  background: var(--view-bg-secondary) !important;
  color: var(--view-text-primary) !important;
}

.dark .message-item.user .message-text {
  background: #409eff !important;
  color: #fff !important;
}

.dark .references-section {
  background: var(--view-bg-secondary) !important;
  border-color: var(--view-border) !important;
}

.dark .references-title {
  color: var(--view-text-regular) !important;
}

.dark .copy-btn,
.dark .feedback-btn {
  color: var(--view-text-secondary) !important;
}

/* Billing 视图 */
.dark .balance-card,
.dark .tier-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .section {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .tier-desc {
  color: var(--view-text-secondary) !important;
}

.dark .tier-item {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .tier-features li {
  color: var(--view-text-regular) !important;
}

/* Profile 视图 */
.dark .profile-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .user-bio {
  color: var(--view-text-secondary) !important;
}

.dark .info-label {
  color: var(--view-text-secondary) !important;
}

.dark .info-value {
  color: var(--view-text-primary) !important;
}

.dark .info-row {
  border-color: var(--view-border) !important;
}

.dark .stat-item {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .stat-label {
  color: var(--view-text-secondary) !important;
}

/* Knowledge 视图 */
.dark .stats-bar {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .file-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .file-name {
  color: var(--view-text-primary) !important;
}

.dark .file-meta,
.dark .file-time {
  color: var(--view-text-secondary) !important;
}

.dark .file-header {
  border-color: var(--view-border) !important;
}

/* Memory 视图 */
.dark .memory-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .memory-header {
  border-color: var(--view-border) !important;
}

.dark .memory-key {
  color: var(--view-text-primary) !important;
}

.dark .memory-value {
  color: var(--view-text-regular) !important;
}

/* History 视图 */
.dark .history-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .message-card {
  background: var(--view-bg) !important;
  border-color: var(--view-border) !important;
}

.dark .card-header {
  border-color: var(--view-border) !important;
}

.dark .card-content {
  color: var(--view-text-primary) !important;
}

.dark .card-time {
  color: var(--view-text-secondary) !important;
}
</style>
