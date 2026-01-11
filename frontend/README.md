# WLOps 前端

WLOps 模型训练与持续演进平台的前端界面。

## 技术栈

- React 18
- TypeScript
- Vite
- Ant Design 5
- React Router 6
- Axios

## 功能特性

### 1. 仪表盘
- 数据集和任务统计概览
- 运行中任务和已完成任务数量
- 最近任务列表

### 2. 数据集管理
- 上传数据集（支持多种格式）
- 查看数据集列表
- 下载数据集
- 删除数据集
- 按领域筛选数据集

### 3. 任务管理
- 创建标准训练任务
- 创建持续学习任务
- 启动/暂停/取消任务
- 实时监控任务状态
- 查看任务执行历史
- 删除已完成的任务

### 4. 任务详情
- 查看任务完整信息
- 实时状态更新（每3秒刷新）
- 执行历史时间线
- 迭代进度跟踪
- 性能指标展示

## 快速开始

### 前置要求

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录

### 预览生产版本

```bash
npm run preview
```

## 配置

### API 代理

开发环境下，前端会自动将 `/api` 请求代理到 `http://localhost:8080`

如需修改后端地址，请编辑 `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:8080',
      changeOrigin: true,
    },
  },
}
```

### 用户 ID

当前版本使用硬编码的用户 ID (userId = 1)。在生产环境中，应该：

1. 实现用户登录功能
2. 从认证 token 中获取用户 ID
3. 在 API 请求中自动携带用户信息

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 公共组件
│   │   └── Layout.tsx       # 布局组件
│   ├── pages/               # 页面组件
│   │   ├── Dashboard.tsx    # 仪表盘
│   │   ├── DatasetList.tsx  # 数据集列表
│   │   ├── TaskList.tsx     # 任务列表
│   │   ├── TaskDetail.tsx   # 任务详情
│   │   └── CreateTask.tsx   # 创建任务
│   ├── services/            # API 服务
│   │   └── api.ts           # API 封装
│   ├── types/               # TypeScript 类型定义
│   │   └── index.ts         # 类型定义
│   ├── utils/               # 工具函数
│   │   └── helpers.ts       # 辅助函数
│   ├── App.tsx              # 应用根组件
│   ├── main.tsx             # 应用入口
│   └── index.css            # 全局样式
├── index.html               # HTML 模板
├── package.json             # 项目配置
├── tsconfig.json            # TypeScript 配置
├── vite.config.ts           # Vite 配置
└── README.md                # 项目文档
```

## 主要功能说明

### 状态管理

当前使用 React Hooks (useState, useEffect) 进行状态管理。对于更复杂的应用，建议引入：
- Redux Toolkit
- Zustand
- Jotai

### 实时更新

- 任务列表：每 5 秒自动刷新
- 任务详情：每 3 秒自动刷新
- 使用 `setInterval` 实现轮询

### 错误处理

- 使用 Ant Design 的 `message` 组件显示错误提示
- API 错误会在控制台输出详细信息
- 建议添加全局错误边界 (Error Boundary)

## 待优化功能

1. 用户认证与授权
2. WebSocket 实时通信（替代轮询）
3. 更详细的错误处理
4. 数据可视化（训练曲线、性能趋势）
5. 批量操作（批量删除、批量启动）
6. 搜索和过滤功能
7. 导出报告功能
8. 暗色主题支持

## 浏览器支持

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 许可证

与主项目保持一致
