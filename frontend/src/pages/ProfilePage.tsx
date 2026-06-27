import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { AuthUser, GenerationProvider } from '../api/client';

const ROLE_LABEL: Record<string, string> = {
  platform_admin: '平台管理员',
  tenant_admin: '团队管理员',
  member: '成员',
};

const PLANS = [
  { name: '免费版', price: '¥0', cur: true, feats: ['每月有限生成', '带水印', '低清导出', '1 个品牌'] },
  { name: 'Pro 版', price: '¥99/月', cur: false, feats: ['更多生成额度', '高清无水印', '多品牌管理', '商用授权说明'] },
  { name: 'Team 版', price: '¥399/月', cur: false, feats: ['多成员协作', '客户审阅链接', '批量生成', '企业素材库'] },
];

const PLATFORMS = ['小红书', '抖音', '淘宝', '京东', '拼多多', '微信', '美团', '亚马逊', '国际站'];

export default function ProfilePage() {
  const [me, setMe] = useState<AuthUser | null>(null);
  const [imgProviders, setImgProviders] = useState<GenerationProvider[]>([]);
  const [videoProviders, setVideoProviders] = useState<GenerationProvider[]>([]);
  // 暂无后端积分接口:mock 一次
  const [credits] = useState(() => 800 + Math.floor(Math.random() * 4200));

  useEffect(() => {
    // providers 接口返回 {providers:[...]},做健壮取数组
    const toArr = (d: unknown): GenerationProvider[] =>
      Array.isArray(d) ? (d as GenerationProvider[]) : ((d as { providers?: GenerationProvider[] })?.providers ?? []);
    api.auth.me().then(setMe).catch(() => setMe(null));
    api.generation.providers().then((d) => setImgProviders(toArr(d))).catch(() => setImgProviders([]));
    api.video.providers().then((d) => setVideoProviders(toArr(d))).catch(() => setVideoProviders([]));
  }, []);

  const realImg = (Array.isArray(imgProviders) ? imgProviders : []).filter((p) => p.name !== 'local');
  const realVideo = (Array.isArray(videoProviders) ? videoProviders : []).filter((p) => p.name !== 'local');
  const display = me?.name || me?.email || me?.phone || 'MOYAG 用户';

  return (
    <div className="min-h-[60vh] px-6 py-8 text-white">
      <div className="mx-auto w-full max-w-3xl space-y-6">
        {/* 账户卡 */}
        <section className="flex items-center gap-4 rounded-3xl border border-white/[0.12] bg-gradient-to-br from-white/[0.1] via-white/[0.05] to-white/[0.02] p-6">
          <div className="grid size-16 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-orange-500 to-rose-500 text-2xl font-bold text-white">
            {display.slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-bold">{display}</h1>
            <p className="truncate text-sm text-gray-400">{me?.email || me?.phone || '未绑定邮箱/手机号'}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full border border-orange-400/30 bg-orange-500/10 px-2.5 py-0.5 text-[11px] text-orange-200">免费版</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] px-2.5 py-0.5 text-[11px] text-gray-300">◆ {credits.toLocaleString()} 积分</span>
              {me && <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] px-2.5 py-0.5 text-[11px] text-gray-300">{ROLE_LABEL[me.role] || me.role}</span>}
            </div>
          </div>
          <button className="shrink-0 rounded-lg border border-white/[0.14] bg-white/[0.05] px-3 py-2 text-xs text-gray-200 transition-colors hover:text-white">升级方案</button>
        </section>

        {/* 套餐对比 */}
        <div className="grid gap-3 sm:grid-cols-3">
          {PLANS.map((p) => (
            <div key={p.name} className={'rounded-2xl border p-4 ' + (p.cur ? 'border-orange-400/40 bg-orange-500/[0.06]' : 'border-white/[0.1] bg-white/[0.04]')}>
              <div className="mb-1 flex items-center justify-between">
                <span className="font-bold text-white">{p.name}</span>
                {p.cur && <span className="rounded-full bg-orange-500/20 px-2 py-0.5 text-[10px] text-orange-200">当前</span>}
              </div>
              <div className="mb-3 text-2xl font-bold text-white">{p.price}</div>
              <ul className="space-y-1.5 text-xs text-gray-400">
                {p.feats.map((f, i) => <li key={i} className="flex items-center gap-1.5"><span className="text-emerald-400">✓</span> {f}</li>)}
              </ul>
            </div>
          ))}
        </div>

        {/* 大模型接口配置(真实 providers) */}
        <section className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-6">
          <h2 className="mb-4 flex items-center gap-2 font-bold text-white">
            <span className="text-orange-300">⚙</span> 大模型接口配置
          </h2>
          <div className="space-y-3 text-sm">
            <Row label="图像生成模型">
              {realImg.length ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">已接入 {realImg.length} 个</span>
              ) : (
                <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-xs text-gray-400">仅本地占位</span>
              )}
            </Row>
            <Row label="视频生成模型">
              {realVideo.length ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-400">已接入 {realVideo.length} 个</span>
              ) : (
                <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-xs text-gray-400">仅本地占位</span>
              )}
            </Row>
          </div>
          {realImg.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5 border-t border-white/[0.08] pt-3">
              {[...realImg, ...realVideo].map((p) => (
                <span key={p.name} className="rounded-full border border-white/[0.1] bg-white/[0.04] px-2.5 py-0.5 text-[11px] text-gray-300">{p.display_name}</span>
              ))}
            </div>
          )}
          <p className="mt-4 rounded-xl bg-white/[0.04] p-3 text-xs leading-relaxed text-gray-500">
            模型路由会按任务类型(图像 / 视频 / 文案 / 版式)自动选择最合适的模型,并支持多模型 fallback 与成本记录。
          </p>
        </section>

        {/* 关于 */}
        <section className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-6">
          <h2 className="mb-2 font-bold text-white">关于 MOYAG</h2>
          <p className="text-sm leading-relaxed text-gray-400">
            MOYAG 是面向中国商家的 AI 品牌与营销设计 Agent,从一句话 brief 自动生成可编辑、可投放、可复用的完整视觉营销资产。
            核心不是「生成图片」,而是「完成设计任务」—— 由多个子 Agent(PM / Research / Brand / Copy / Visual / Image / Layout / Video / Mockup / Compliance / Export)协作完成理解、调研、策略、创意、生成、画布组织、合规与导出。
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {PLATFORMS.map((p) => <span key={p} className="rounded-full border border-white/[0.1] px-2 py-0.5 text-[11px] text-gray-400">{p}</span>)}
          </div>
        </section>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-white/[0.06] py-2 last:border-0">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium">{children}</span>
    </div>
  );
}
