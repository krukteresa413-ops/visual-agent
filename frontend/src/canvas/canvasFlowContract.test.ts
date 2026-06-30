import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(__dirname, '..');

function read(relativePath: string) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
}

describe('S3 React Flow canvas contract', () => {
  it('routes VITE_ENABLE_FLOW_CANVAS=true to CanvasFlow and keeps legacy fallback', () => {
    const wrapper = read('components/CanvasView.tsx');

    expect(wrapper).toContain('VITE_ENABLE_FLOW_CANVAS');
    expect(wrapper).toContain('CanvasFlow');
    expect(wrapper).toContain('CanvasViewLegacy');
    expect(wrapper).toMatch(/useFlowCanvas[\s\S]*\?[\s\S]*<CanvasFlow/);
  });

  it('CanvasFlow uses React Flow as the runtime state and loads legacy canvas-state through adapters', () => {
    const flow = read('components/CanvasFlow.tsx');

    expect(flow).toContain('@xyflow/react');
    expect(flow).toContain('useNodesState');
    expect(flow).toContain('useEdgesState');
    expect(flow).toContain('legacyToFlowCanvas');
    expect(flow).toContain('api.atelierCanvas.getState');
    expect(flow).not.toContain('useState<CanvasElement[]');
    expect(flow).not.toContain('setElements(');
    expect(flow).not.toContain('persistCanvas');
  });

  it('AssetNode exposes stable DOM markers for browser verification', () => {
    const assetNode = read('components/nodes/AssetNode.tsx');

    expect(assetNode).toContain('data-flow-asset-node');
    expect(assetNode).toContain('thumbnail_url');
    expect(assetNode).toContain('asset_ref');
    expect(assetNode).toContain('metadata');
  });

  it('CanvasFlow persists through useCanvasPersistence and does not save from legacy fallback', () => {
    const flow = read('components/CanvasFlow.tsx');
    const persistence = read('canvas/useCanvasPersistence.ts');

    expect(flow).toContain('useCanvasPersistence');
    expect(flow).toContain('saveCanvas');
    expect(persistence).toContain('api.atelierCanvas.saveState');
    expect(persistence).toContain('flowToLegacyCanvas');
  });

  it('CanvasFlow sends React Flow selection context to AI Companion', () => {
    const flow = read('components/CanvasFlow.tsx');

    expect(flow).toContain('buildSelectionContext');
    expect(flow).toContain('data-ai-companion');
    expect(flow).toContain('data-selected-count');
    expect(flow).toContain('data-selected-asset-ids');
    expect(flow).toContain('onSelectionChange={noteSelectionChange}');
  });

  it('CanvasFlow drag-save persists the full React Flow node set, not the drag callback subset', () => {
    const flow = read('components/CanvasFlow.tsx');

    expect(flow).toContain('getNodes() as typeof nodes');
    expect(flow).not.toContain('currentNodes as typeof nodes');
  });

  it('CanvasFlow runs canvas actions through existing async task/progress APIs and backfills a variant node plus edge', () => {
    const flow = read('components/CanvasFlow.tsx');
    const client = read('api/client.ts');

    expect(client).toContain('canvasActions');
    expect(client).toContain("client.post('/canvas-actions'");
    expect(client).toContain("client.get(`/canvas-actions/${taskId}`)");
    expect(flow).toContain('runCanvasAction');
    expect(flow).toContain('api.canvasActions.start');
    expect(flow).toContain('api.canvasActions.poll');
    expect(flow).toContain('api.progress.streamUrl');
    expect(flow).toContain('upsertFlowCanvasNode');
    expect(flow).toContain('variant_of');
    expect(flow).toContain('nextEdge.relation_type ||');
    expect(flow).toContain('data-ai-action-input');
    expect(flow).toContain('data-ai-action-run');
  });

  it('GeneratePage ModelPreferencePanel renders API-backed model cards and passes selected model to quick-generate', () => {
    const page = read('pages/GeneratePage.tsx');
    const modelPanel = read('components/model/ModelPreferencePanel.tsx');

    expect(page).toContain("queryKey: ['generation', 'models', 'catalog']");
    expect(page).toContain('ModelPreferencePanel');
    expect(modelPanel).toContain('data-model-preference-panel');
    expect(modelPanel).toContain('data-model-card');
    expect(modelPanel).toContain('data-model-unavailable');
    expect(page).toContain('image_model: autoModel ? undefined : selectedImageModel || undefined');
    expect(page).toContain('api.generation.catalog');
    expect(page).not.toContain('GPT Image');
    expect(page).not.toContain('Seedance');
    expect(page).not.toContain('Kling');
  });


  it('does not refit or relayout nodes when selection changes', () => {
    const flow = read('components/CanvasFlow.tsx');
    const selectionHandler = flow.slice(flow.indexOf('const noteSelectionChange'), flow.indexOf('const applyCanvasActionResult'));

    expect(selectionHandler).not.toContain('setNodes');
    expect(selectionHandler).not.toContain('fitView');
    expect(selectionHandler).not.toContain('layout');
    expect(flow).not.toContain('fitView={nodes.length > 0}');
    expect(flow).not.toContain('fitViewOptions');
  });


  it('CanvasFlow renders editable relation edges for prompt labels', () => {
    const flow = read('components/CanvasFlow.tsx');
    const editableEdge = read('components/canvas/EditableRelationEdge.tsx');

    expect(flow).toContain('EditableRelationEdge');
    expect(flow).toContain('edgeTypes');
    expect(flow).toContain("editableRelation");
    expect(flow).toContain("type: 'editableRelation'");
    expect(flow).toContain('onRelationLabelCommit');
    expect(editableEdge).toContain('data-editable-relation-edge');
    expect(editableEdge).toContain('data-relation-label-input');
    expect(editableEdge).toContain('onLabelCommit');
  });


  it('AssetNode renders generated video nodes with native video controls', () => {
    const assetNode = read('components/nodes/AssetNode.tsx');

    expect(assetNode).toContain("node.type === 'video'");
    expect(assetNode).toContain('<video');
    expect(assetNode).toContain('controls');
    expect(assetNode).toContain('data-flow-video-node');
  });


  it('CanvasFlow passes selected source imageUrl to canvas actions and displays instruction-labeled lineage', () => {
    const selection = read('canvas/selectionContext.ts');
    const flow = read('components/CanvasFlow.tsx');
    const editableEdge = read('components/canvas/EditableRelationEdge.tsx');

    expect(selection).toContain('imageUrl?: string');
    expect(selection).toContain('imageUrl: extractImageUrl(node.data)');
    expect(flow).toContain('data.instruction');
    expect(editableEdge).toContain('instruction?: string');
    expect(editableEdge).toContain('relationData.instruction');
  });

  it('CanvasFlow wires a unified commit layer, undo/redo history and editor keyboard shortcuts', () => {
    const flow = read('components/CanvasFlow.tsx');
    const history = read('canvas/history.ts');

    // 统一提交层:语义操作走 commit(更新 state + 入栈 + 持久化)
    expect(flow).toContain('useCanvasHistory');
    expect(flow).toContain('const commit = useCallback');
    expect(flow).toContain('pushHistory');
    expect(flow).toContain('resetHistory');
    // 撤销/重做 UI(浏览器验证锚点)
    expect(flow).toContain('data-canvas-undo');
    expect(flow).toContain('data-canvas-redo');
    // 关掉 React Flow 内置删除,改走可撤销 + 持久化的自有删除
    expect(flow).toContain('deleteKeyCode={null}');
    expect(flow).toContain('deleteSelected');
    // 快捷键:Undo(z) / Redo(y)
    expect(flow).toMatch(/key === 'z' \|\| e\.key === 'Z'/);
    // 历史栈纯函数对外契约
    expect(history).toContain('export function record');
    expect(history).toContain('export function undo');
    expect(history).toContain('export function redo');
  });

});
