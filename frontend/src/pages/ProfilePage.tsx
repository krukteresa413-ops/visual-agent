import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { AuthUser, GenerationProvider, RechargeTier } from '../api/client';

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
  // 真实积分余额(后端 /credits/balance)
  const [credits, setCredits] = useState(0);
  const [tiers, setTiers] = useState<RechargeTier[]>([]);
  const [showRecharge, setShowRecharge] = useState(false);
  const [payingFen, setPayingFen] = useState<number | null>(null);
  const [payError, setPayError] = useState<string | null>(null);

  useEffect(() => {
    // providers 接口返回 {providers:[...]},做健壮取数组
    const toArr = (d: unknown): GenerationProvider[] =>
      Array.isArray(d) ? (d as GenerationProvider[]) : ((d as { providers?: GenerationProvider[] })?.providers ?? []);
    api.auth.me().then(setMe).catch(() => setMe(null));
    api.credits.balance().then((d) => setCredits(d.credits)).catch(() => setCredits(0));
    api.payment.tiers().then(setTiers).catch(() => setTiers([]));
    api.generation.providers().then((d) => setImgProviders(toArr(d))).catch(() => setImgProviders([]));
    api.video.providers().then((d) => setVideoProviders(toArr(d))).catch(() => setVideoProviders([]));
  }, []);

  const recharge = async (amountFen: number) => {
    setPayingFen(amountFen);
    setPayError(null);
    try {
      const order = await api.payment.createAlipay(amountFen);
      window.location.href = order.pay_url; // 跳转支付宝沙箱收银台
    } catch (e) {
      const status = (e as { response?: { status?: number } })?.response?.status;
      setPayError(status === 503 ? '支付宝沙箱尚未配置(请先在 .env 填入沙箱密钥)' : '下单失败,请稍后重试');
      setPayingFen(null);
    }
  };

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
              <button
                onClick={() => { setPayError(null); setShowRecharge(true); }}
                className="inline-flex items-center gap-1 rounded-full border border-orange-400/40 bg-orange-500/15 px-2.5 py-0.5 text-[11px] text-orange-200 transition-colors hover:bg-orange-500/25"
              >
                + 充值
              </button>
              {me && <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] px-2.5 py-0.5 text-[11px] text-gray-300">{ROLE_LABEL[me.role] || me.role}</span>}
            </div>
          </div>
          <button className="shrink-0 rounded-lg border border-white/[0.14] bg-white/[0.05] px-3 py-2 text-xs text-gray-200 transition-colors hover:text-white">升级方案</button>
        </section>

        {/* 数据看板入口(从顶部导航移入个人中心) */}
        <Link
          to="/dashboard"
          className="flex items-center justify-between rounded-2xl border border-white/[0.1] bg-white/[0.04] p-5 transition-colors hover:border-orange-400/40 hover:bg-orange-500/[0.06]"
        >
          <span className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-orange-500/15 text-xl">📊</span>
            <span>
              <span className="block font-semibold text-white">数据看板</span>
              <span className="block text-xs text-gray-400">项目统计与爆款趋势</span>
            </span>
          </span>
          <span className="text-gray-400">→</span>
        </Link>

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

      {/* 充值弹窗 */}
      {showRecharge && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4"
          onClick={() => payingFen === null && setShowRecharge(false)}
        >
          <div
            className="w-full max-w-md rounded-3xl border border-white/[0.12] bg-[#15151b] p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-1 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">充值积分</h3>
              <button
                onClick={() => payingFen === null && setShowRecharge(false)}
                className="rounded-lg px-2 py-1 text-gray-400 transition-colors hover:text-white"
              >
                ✕
              </button>
            </div>
            <p className="mb-4 text-xs text-gray-500">选择档位,支付宝沙箱完成支付后积分自动到账。</p>
            <div className="grid grid-cols-2 gap-3">
              {tiers.map((t) => (
                <button
                  key={t.amount_fen}
                  disabled={payingFen !== null}
                  onClick={() => recharge(t.amount_fen)}
                  className="rounded-2xl border border-white/[0.12] bg-white/[0.04] p-4 text-left transition-colors hover:border-orange-400/50 hover:bg-orange-500/[0.06] disabled:opacity-50"
                >
                  <div className="text-xl font-bold text-white">{t.label}</div>
                  <div className="mt-1 text-xs text-orange-200">◆ {t.credits.toLocaleString()} 积分</div>
                  {payingFen === t.amount_fen && <div className="mt-1 text-[11px] text-gray-400">跳转支付中…</div>}
                </button>
              ))}
            </div>
            {tiers.length === 0 && <p className="mt-4 text-center text-sm text-gray-500">暂无可用档位</p>}
            {payError && <p className="mt-4 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-300">{payError}</p>}
          </div>
        </div>
      )}
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
