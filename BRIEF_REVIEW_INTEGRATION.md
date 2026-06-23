# BriefReviewPanel 集成说明

## 已完成的文件修改

### 1. types/index.ts
新增字段到 ProductBrief 接口：
- brand_name（品牌名）
- target_audience（目标受众）
- target_country（目标国家/地区）
- cultural_taboos（文化禁忌）
- publish_platform（发布平台）
- scheduled_date（预发布日期）
- promotional_event（促销活动，自动推断）

### 2. components/BriefReviewPanel.tsx（新建）
核心功能：
- 12个字段的卡片式网格展示（3列/2列/1列响应式）
- 空缺字段显示橙色虚线边框 + ⚠️图标
- 已填充字段显示正常边框 + 编辑图标
- 点击字段进入inline编辑模式（text/textarea/date）
- scheduled_date 变化时自动推断 promotional_event（618/双11/双12/女神节/520）
- 底部操作按钮：【确认并生成】【重新上传】

### 3. pages/GeneratePage.tsx
集成逻辑：
- 导入 BriefReviewPanel 组件
- 新增状态：showReview（控制显示审核面板）
- DocumentUploader 和 BriefParsePanel 回调中设置 showReview=true
- showReview 为 true 时展示 BriefReviewPanel，隐藏 BriefForm
- onConfirm 回调：更新 brief，隐藏面板，返回手动模式
- onReupload 回调：清空 brief，隐藏面板

### 4. index.css
新增动画：
- fadeIn 动画（0.5s ease-out）
- animate-fadeIn 类

## 工作流程

1. 用户上传文档 → DocumentUploader 解析
2. 解析完成 → 触发 onParsed 回调 → setShowReview(true)
3. 显示 BriefReviewPanel（带淡入动画）
4. 用户查看/编辑字段：
   - 点击字段卡片进入编辑模式
   - text/date 类型：input 框
   - tags 类型：textarea（逗号分隔）
   - 编辑完成：失焦或按 Enter 自动保存
5. 用户点击【确认并生成】→ 返回手动模式，BriefForm 继续可编辑
6. 用户点击【重新上传】→ 清空数据，重新上传

## 样式规范
- 遵循 MOYAG liquid-card 风格
- 空缺字段：border-2 border-dashed border-orange-500/50 bg-orange-950/10
- 已填充字段：border border-white/10 bg-white/5
- 过渡动画：0.5s
- 响应式网格：lg:grid-cols-3 md:grid-cols-2 grid-cols-1

## 促销活动推断规则
- 6.15-6.20 → 618购物节
- 11.9-11.12 → 双十一
- 12.10-12.14 → 双十二
- 3.6-3.10 → 女神节
- 5.20 → 520
