import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, clearToken, getToken, setToken } from '../api/client';
import ThemeToggle, { useTheme } from '../components/ThemeToggle';

// ============================================================
// AuthPage 组件 — 双模式：模态浮层 (有 onClose) / 独立页面 (无 onClose)
// ============================================================
export default function AuthPage({ onClose }: { onClose?: () => void }) {
  const navigate = useNavigate();
  const { isLight, toggle: toggleTheme } = useTheme();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [identifier, setIdentifier] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [currentUser, setCurrentUserState] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);

  // 淡入动画
  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  useEffect(() => { setError(''); setSuccess(''); }, [mode]);
  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    api.auth.me()
      .then(user => {
        if (!cancelled) setCurrentUserState(user.email || user.phone || user.name || null);
      })
      .catch(() => {
        clearToken();
        if (!cancelled) setCurrentUserState(null);
      });
    return () => { cancelled = true; };
  }, []);


  const handleClose = () => {
    setVisible(false);
    setTimeout(() => {
      if (onClose) onClose();
      else navigate('/');
    }, 200);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');
    if (!identifier.trim() || !password.trim()) { setError('请填写邮箱/手机号和密码'); return; }
    try {
      const result = await api.auth.login({ identifier: identifier.trim(), password });
      const accountLabel = result.user.email || result.user.phone || '';
      setToken(result.access_token);
      setCurrentUserState(accountLabel);
      setSuccess('✅ 欢迎回来，' + (result.user.name || accountLabel));
      setTimeout(() => handleClose(), 300);
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败');
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');
    if ((!email.trim() && !phone.trim()) || !password.trim() || !confirmPassword.trim()) {
      setError('请填写邮箱或中国手机号，以及密码'); return;
    }
    if (password !== confirmPassword) { setError('两次密码不一致'); return; }
    if (password.length < 8) { setError('密码至少8位'); return; }
    try {
      const cleanEmail = email.trim().toLowerCase();
      const cleanPhone = phone.trim();
      const displayName = name.trim() || cleanEmail.split('@')[0] || cleanPhone;
      await api.auth.register({
        ...(cleanEmail ? { email: cleanEmail } : {}),
        ...(cleanPhone ? { phone: cleanPhone } : {}),
        password,
        name: displayName,
        tenant_name: displayName,
      });
      const result = await api.auth.login({ identifier: cleanEmail || cleanPhone, password });
      const accountLabel = result.user.email || result.user.phone || '';
      setToken(result.access_token);
      setCurrentUserState(accountLabel);
      setSuccess('🎉 注册成功！');
      setTimeout(() => handleClose(), 300);
    } catch (err: any) {
      setError(err.response?.data?.detail || '注册失败');
    }
  };

  const handleSwitchAccount = () => {
    clearToken();
    setCurrentUserState(null);
    setSuccess('已退出当前账号，请登录新账号');
  };

  const handleLogout = () => {
    clearToken();
    setCurrentUserState(null);
    setSuccess('已退出登录');
  };

  const isModal = !!onClose;
  const pageBg = isLight
    ? 'linear-gradient(135deg, #f8fafc 0%, #fff7ed 46%, #f8fafc 100%)'
    : 'linear-gradient(135deg, #08090b 0%, #101114 52%, #08090b 100%)';
  const brandText = isLight ? 'text-gray-950' : 'text-white/90';
  const mutedText = isLight ? 'text-gray-500' : 'text-gray-500';
  const cardClass = isLight
    ? 'backdrop-blur-2xl bg-white/85 border border-gray-200/80 rounded-2xl p-5 shadow-[0_24px_80px_rgba(15,23,42,0.12),inset_0_1px_0_0_rgba(255,255,255,0.85)]'
    : 'backdrop-blur-2xl bg-neutral-950/78 border border-white/[0.08] rounded-2xl p-5 shadow-[0_28px_90px_rgba(0,0,0,0.56),inset_0_1px_0_0_rgba(255,255,255,0.05)]';
  const surfaceClass = isLight
    ? 'bg-gray-50/90 border border-gray-200/80'
    : 'bg-white/[0.035] border border-white/[0.07]';
  const inputClass = 'w-full px-3 py-2 rounded-lg text-[13px] focus:outline-none focus:border-orange-500/50 focus:ring-1 focus:ring-orange-500/20 transition-all ' +
    (isLight
      ? 'bg-white border border-gray-200 text-gray-950 placeholder-gray-400'
      : 'bg-white/[0.04] border border-white/[0.08] text-white placeholder-gray-600');
  const labelClass = 'block text-[10px] mb-1 ' + mutedText;

  const content = (
    <div className={'relative z-10 w-full max-w-md transition-all duration-300 ' +
      (visible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-[0.97]')
    }>
      {/* Logo */}
      <div className="text-center mb-5">
        <div className="flex items-center justify-center gap-2 mb-1.5">
          <img src="/logo.png" alt="MOYAG" className="w-7 h-7 rounded-lg" />
          <span className={'font-semibold text-base tracking-tight ' + brandText}>MOYAG</span>
        </div>
        <p className={'text-[10px] tracking-[0.18em] uppercase ' + mutedText}>Account Center</p>
      </div>

      {/* 主卡片 */}
      <div className={cardClass}>
        {!isModal && (
          <div className="mb-3 flex justify-end">
            <ThemeToggle isLight={isLight} toggle={toggleTheme} />
          </div>
        )}

        {/* 当前登录状态 */}
        {currentUser && (
          <div className={'mb-4 p-3 rounded-xl ' + surfaceClass}>
            <div className="flex items-center justify-between">
              <div>
                <p className={'text-[10px] ' + mutedText}>当前账号</p>
                <p className={'text-sm font-medium ' + (isLight ? 'text-gray-900' : 'text-white/80')}>{currentUser}</p>
              </div>
              <div className="flex gap-1.5">
                <button onClick={handleSwitchAccount}
                  className="text-[10px] px-2.5 py-1 rounded-lg bg-orange-500/20 text-orange-400 border border-orange-500/30 hover:bg-orange-500/30 transition-colors">
                  切换账号
                </button>
                <button onClick={handleLogout}
                  className={'text-[10px] px-2.5 py-1 rounded-lg transition-colors ' + (isLight ? 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200' : 'bg-white/[0.05] text-gray-400 border border-white/[0.08] hover:bg-white/[0.08]')}>
                  退出
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 错误/成功提示 */}
        {error && (
          <div className="mb-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-[11px] text-red-400">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-3 p-2.5 rounded-lg bg-green-500/10 border border-green-500/20 text-[11px] text-green-400">
            {success}
          </div>
        )}

        {/* 模式切换 */}
        <div className={'flex mb-4 rounded-lg p-0.5 ' + (isLight ? 'bg-gray-100 border border-gray-200/80' : 'bg-white/[0.04]')}>
          <button onClick={() => setMode('login')}
            className={'flex-1 py-1.5 text-[11px] font-medium rounded-md transition-all ' +
              (mode === 'login' ? (isLight ? 'bg-white text-gray-950 shadow-sm' : 'bg-white/[0.08] text-white') : (isLight ? 'text-gray-500 hover:text-gray-800' : 'text-gray-500 hover:text-gray-300'))
            }>
            登录
          </button>
          <button onClick={() => setMode('register')}
            className={'flex-1 py-1.5 text-[11px] font-medium rounded-md transition-all ' +
              (mode === 'register' ? (isLight ? 'bg-white text-gray-950 shadow-sm' : 'bg-white/[0.08] text-white') : (isLight ? 'text-gray-500 hover:text-gray-800' : 'text-gray-500 hover:text-gray-300'))
            }>
            注册
          </button>
        </div>

        {/* 登录表单 */}
        {mode === 'login' && (
          <form onSubmit={handleLogin} className="space-y-2.5">
            <div>
              <label className={labelClass}>邮箱或中国手机号</label>
              <input type="text" value={identifier} onChange={e => setIdentifier(e.target.value)}
                placeholder="your@email.com / 13800138000"
                className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>密码</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder="输入密码"
                className={inputClass} />
            </div>
            <button type="submit"
              className="w-full py-2 bg-orange-500 text-white text-[13px] font-medium rounded-lg hover:bg-orange-400 transition-all shadow-lg shadow-orange-500/20">
              登录
            </button>
          </form>
        )}

        {/* 注册表单 */}
        {mode === 'register' && (
          <form onSubmit={handleRegister} className="space-y-2.5">
            <div>
              <label className={labelClass}>昵称</label>
              <input type="text" value={name} onChange={e => setName(e.target.value)}
                placeholder="你的名字（选填）"
                className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>邮箱（邮箱或手机号二选一）</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>中国手机号（邮箱或手机号二选一）</label>
              <input type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                placeholder="13800138000"
                className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>密码</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                placeholder="至少8位"
                className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>确认密码</label>
              <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                className={inputClass} />
            </div>
            <button type="submit"
              className="w-full py-2 bg-orange-500 text-white text-[13px] font-medium rounded-lg hover:bg-orange-400 transition-all shadow-lg shadow-orange-500/20">
              注册
            </button>
          </form>
        )}

        {/* 底部关闭 */}
        <button onClick={handleClose}
          className={'mt-3 w-full py-1.5 text-[10px] transition-colors ' + (isLight ? 'text-gray-400 hover:text-gray-700' : 'text-gray-600 hover:text-gray-400')}>
          {isModal ? '✕ 关闭' : '← 返回首页'}
        </button>
      </div>

      {/* 测试入口说明 — 仅独立页面模式 */}
      {!isModal && (
        <p className={'text-center mt-4 text-[10px] ' + (isLight ? 'text-gray-400' : 'text-gray-700')}>
          支持邮箱或中国手机号注册 · 当前为密码登录，短信验证码后续可接入
        </p>
      )}
    </div>
  );

  // 模态浮层模式
  if (isModal) {
    return (
      <div
        className={'fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ' +
          (visible ? 'bg-black/60 backdrop-blur-md' : 'bg-black/0 backdrop-blur-none')
        }
        onClick={handleClose}
      >
        {/* 背景光晕 */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-orange-500/8 rounded-full blur-[100px]" />
          <div className="absolute bottom-1/4 right-1/4 w-56 h-56 bg-neutral-500/6 rounded-full blur-[80px]" />
        </div>
        <div onClick={e => e.stopPropagation()}>
          {content}
        </div>
      </div>
    );
  }

  // 独立页面模式
  return (
    <div className="min-h-screen flex items-center justify-center px-4"
      style={{ background: pageBg }}>
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-orange-500/10 rounded-full blur-[120px]" />
        <div className={"absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full blur-[100px] " + (isLight ? 'bg-stone-300/30' : 'bg-neutral-500/8')} />
      </div>
      {content}
    </div>
  );
}
