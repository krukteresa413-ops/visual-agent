import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const pageSource = fs.readFileSync(path.resolve(__dirname, 'GeneratePage.tsx'), 'utf8');
const legacyCanvasSource = fs.readFileSync(path.resolve(__dirname, '../components/CanvasViewLegacy.tsx'), 'utf8');

describe('canvas UX cleanup contract', () => {
  it('keeps compare and font actions but removes inert hand/text toolbar buttons', () => {
    expect(legacyCanvasSource).toContain('onToggleCompare');
    expect(legacyCanvasSource).toContain('onOpenFont');
    expect(legacyCanvasSource).toContain('比较');
    expect(legacyCanvasSource).toContain('字体');
    expect(legacyCanvasSource).not.toContain("{ label: '抓手'");
    expect(legacyCanvasSource).not.toContain("{ label: '文字'");
  });

  it('only shows the reference-image drop overlay for external file drags', () => {
    expect(pageSource).toContain('isExternalFileDrag');
    expect(pageSource).toContain("e.dataTransfer.types.includes('Files')");
    expect(pageSource).not.toContain(`const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };`);
  });

  it('production legacy canvas renders editable relation labels', () => {
    expect(legacyCanvasSource).toContain('data-editable-relation-edge');
    expect(legacyCanvasSource).toContain('data-relation-label-input');
    expect(legacyCanvasSource).toContain('onLabelChange');
    expect(legacyCanvasSource).toContain('persistCanvas(elements, nextConnections, viewport)');
  });


  it('does not save stale element positions on drag release', () => {
    const mouseUpStart = legacyCanvasSource.indexOf('const handleMouseUp = () => {');
    const panBranchStart = legacyCanvasSource.indexOf('if (dragging) {', mouseUpStart);
    const elementDragBranch = legacyCanvasSource.slice(mouseUpStart, panBranchStart);
    expect(elementDragBranch).toContain('if (draggingElId)');
    expect(elementDragBranch).toContain('return;');
    expect(elementDragBranch).not.toContain('persistCanvas(elements, connections, viewport)');
    expect(legacyCanvasSource).toContain('persistCanvas(next, connections, viewport)');
  });


  it('does not create default next connections or text-only graphic placeholder nodes', () => {
    expect(legacyCanvasSource).toContain('function buildDefaultConnections(_elements: CanvasElement[]): CanvasConnection[]');
    expect(legacyCanvasSource).not.toContain("label: i === 0 ? 'next' : ''");
    expect(legacyCanvasSource).toContain("if (!sp?.url && !sp?.thumbnail_url) return;");
    expect(legacyCanvasSource).toContain('if (props.adMaterial?.url || props.adMaterial?.thumbnail_url)');
    expect(legacyCanvasSource).not.toContain("if (props.adMaterial) add('ad', 'graphic', 'Ad Material', props.adMaterial, 260, 220);");
  });

});
