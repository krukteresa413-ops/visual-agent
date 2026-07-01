import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const pagePath = path.resolve(__dirname, 'ProjectsPage.tsx');
const source = fs.readFileSync(pagePath, 'utf8');

describe('ProjectsPage center new canvas entry', () => {
  it('creates an empty project through the existing projects API before navigating to the canvas', () => {
    expect(source).toContain("import { api, getToken } from '../api/client'");
    expect(source).toContain('const createEmptyCanvasProject = async () =>');
    expect(source).toContain("api.projects.create('未命名项目', '')");
    expect(source).toContain("navigate(`/generate/${project.id}`)");
  });

  it('does not open the quick prompt modal from the center + new button', () => {
    expect(source).toMatch(/<button onClick=\{createEmptyCanvasProject\}[\s\S]*?新建/);
    expect(source).not.toContain('onClick={() => setShowQuickGen(true)}');
  });
});

describe('ProjectsPage quick generation review bypass', () => {
  it('does not block homepage text generation when generate-from-document asks for review', () => {
    expect(source).not.toContain('if (data.needs_review)');
    expect(source).not.toContain('setReviewQuestions(data.questions || [])');
    expect(source).toContain("navigate('/generate/new', { state: { quickMode: true");
  });
});

describe('CanvasView generated result merge contract', () => {
  it('keeps newly generated result images visible even when saved canvas state exists', () => {
    const canvasSource = fs.readFileSync(path.resolve(__dirname, '../components/CanvasViewLegacy.tsx'), 'utf8');
    expect(canvasSource).toContain('mergeGeneratedElements');
    expect(canvasSource).toContain('persistCanvas(next, connections, viewport)');
  });
});
