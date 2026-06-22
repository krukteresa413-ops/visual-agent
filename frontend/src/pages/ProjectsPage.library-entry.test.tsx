import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const pagesRoot = __dirname;
const componentsRoot = path.resolve(__dirname, '../components');
const projectsPage = fs.readFileSync(path.join(pagesRoot, 'ProjectsPage.tsx'), 'utf8');
const generatePage = fs.readFileSync(path.join(pagesRoot, 'GeneratePage.tsx'), 'utf8');
const libraryPanel = fs.existsSync(path.join(componentsRoot, 'LibraryPanel.tsx'))
  ? fs.readFileSync(path.join(componentsRoot, 'LibraryPanel.tsx'), 'utf8')
  : '';
const inspirationPanel = fs.existsSync(path.join(componentsRoot, 'InspirationPanel.tsx'))
  ? fs.readFileSync(path.join(componentsRoot, 'InspirationPanel.tsx'), 'utf8')
  : '';

describe('homepage library information architecture', () => {
  it('renames the former brand diamond to the library entry without changing the other diamonds', () => {
    expect(projectsPage).toContain("{ title: '资料库', desc: '品牌·产品·灵感', icon: '📚', action: 'library' }");
    expect(projectsPage).toContain("{ title: '灵感库', desc: '创意灵感', icon: '💡', action: 'inspiration' }");
    expect(projectsPage).toContain("{ title: '个人中心', desc: '账户与积分', icon: '👤', action: 'profile' }");
    expect(projectsPage).toContain("{ title: '项目库', desc: '项目陈列柜', icon: '📁', action: 'projects' }");
    expect(projectsPage).not.toContain("title: '品牌套件'");
    expect(projectsPage).not.toContain("desc: '品牌管理'");
  });

  it('opens a library panel that embeds the existing brand kit as the brand assets section', () => {
    expect(projectsPage).toContain("action === 'library'");
    expect(projectsPage).toContain('setShowLibrary(true)');
    expect(projectsPage).toContain('<LibraryPanel');
    expect(libraryPanel).toContain("import BrandKitPanel from './BrandKitPanel'");
    expect(libraryPanel).toContain('品牌资产');
    expect(libraryPanel).toContain('产品资料');
    expect(libraryPanel).toContain('公司资料');
    expect(libraryPanel).toContain('销售 SOP');
    expect(libraryPanel).toContain('敬请完善');
  });

  it('renames the canvas right panel brand tab to library and keeps BrandKit under brand assets', () => {
    expect(generatePage).toContain('data-right-panel-trigger="library"');
    expect(generatePage).toContain('🎨 资料库');
    expect(generatePage).toContain("rightPanel === 'library'");
    expect(generatePage).toContain('<LibraryPanel');
    expect(generatePage).not.toContain('data-right-panel-trigger="brand"');
    expect(generatePage).not.toContain('>🎨 品牌</button>');
  });
});


describe('homepage project gallery single-click entry', () => {
  it('opens a showcase-style project gallery instead of the old create-project modal', () => {
    expect(projectsPage).toContain("{ title: '项目库', desc: '项目陈列柜', icon: '📁', action: 'projects' }");
    expect(projectsPage).toContain('setShowProjectGallery(true)');
    expect(projectsPage).not.toContain("else if (action === 'projects') { setShowCreate(true); return; }");
    expect(projectsPage).toContain('data-project-gallery');
    expect(projectsPage).toContain('项目陈列柜');
    expect(projectsPage).toContain('继续你的视觉创作项目');
    expect(projectsPage).toContain('project-gallery-card');
    expect(projectsPage).toContain('ProjectGallery');
  });

  it('keeps gallery actions short and visual: continue canvas plus light new project entry', () => {
    expect(projectsPage).toContain('继续创作');
    expect(projectsPage).toContain('新建项目');
    expect(projectsPage).toContain('最近项目');
    expect(projectsPage).toContain('空白画布');
    expect(projectsPage).toContain('项目封面');
  });
});


describe('homepage inspiration gallery single-click entry', () => {
  it('uses the same gallery design language as project gallery when the inspiration diamond is clicked', () => {
    expect(projectsPage).toContain("else if (action === 'inspiration') { setShowInspiration(true); return; }");
    expect(projectsPage).toContain('<InspirationPanel');
    expect(inspirationPanel).toContain('data-inspiration-gallery');
    expect(inspirationPanel).toContain('Inspiration Gallery');
    expect(inspirationPanel).toContain('灵感陈列柜');
    expect(inspirationPanel).toContain('像逛作品集一样挑选创意参考');
    expect(inspirationPanel).toContain('inspiration-gallery-card');
    expect(inspirationPanel).toContain('backdrop-blur-xl');
    expect(inspirationPanel).toContain('bg-black/60');
  });

  it('keeps the original prompt reuse actions after the visual redesign', () => {
    expect(inspirationPanel).toContain('直接复用原 Prompt');
    expect(inspirationPanel).toContain('参数化后生成');
    expect(inspirationPanel).toContain('onUseStyle(buildParameterizedPrompt(), selected)');
  });
});


describe('homepage profile gallery single-click entry', () => {
  it('opens profile center with the same gallery design language as project and inspiration entries', () => {
    expect(projectsPage).toContain("else if (action === 'profile') { setShowProfile(true); return; }");
    expect(projectsPage).toContain('data-profile-gallery');
    expect(projectsPage).toContain('Profile Gallery');
    expect(projectsPage).toContain('个人陈列柜');
    expect(projectsPage).toContain('账户、积分和创作资产集中管理');
    expect(projectsPage).toContain('profile-gallery-card');
    expect(projectsPage).toContain('bg-black/60');
    expect(projectsPage).toContain('backdrop-blur-xl');
    expect(projectsPage).not.toContain('max-w-xs mx-4 space-y-4 rounded-2xl');
  });

  it('keeps dashboard and history as explicit profile gallery actions', () => {
    expect(projectsPage).toContain('创作总览');
    expect(projectsPage).toContain('历史记录');
    expect(projectsPage).toContain('账户设置');
    expect(projectsPage).toContain('积分中心');
    expect(projectsPage).toContain('to="/dashboard"');
    expect(projectsPage).toContain('to="/history"');
  });
});


describe('homepage library gallery single-click entry', () => {
  it('uses the same gallery design language as project/inspiration/profile entries', () => {
    expect(projectsPage).toContain("action === 'library'");
    expect(projectsPage).toContain('<LibraryPanel');
    expect(libraryPanel).toContain('data-library-gallery');
    expect(libraryPanel).toContain('Library Gallery');
    expect(libraryPanel).toContain('资料陈列柜');
    expect(libraryPanel).toContain('品牌、产品、公司与销售资料集中陈列');
    expect(libraryPanel).toContain('library-gallery-card');
    expect(libraryPanel).toContain('bg-black/60');
    expect(libraryPanel).toContain('backdrop-blur-xl');
  });

  it('keeps brand assets as the first-class built-in section and preserves other library sections', () => {
    expect(libraryPanel).toContain('品牌资产');
    expect(libraryPanel).toContain('产品资料');
    expect(libraryPanel).toContain('公司资料');
    expect(libraryPanel).toContain('销售 SOP');
    expect(libraryPanel).toContain("import BrandKitPanel from './BrandKitPanel'");
    expect(libraryPanel).toContain('<BrandKitPanel');
    expect(libraryPanel).toContain('打开品牌资产');
    expect(libraryPanel).toContain('敬请完善');
  });
});
