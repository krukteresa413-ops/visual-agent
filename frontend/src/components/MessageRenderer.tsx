import type { ChatMessage } from '../lib/sse/chatReducer';

type Props = {
  message: ChatMessage;
  isLight?: boolean;
};

export default function MessageRenderer({ message, isLight = true }: Props) {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const shellStyle = isUser
    ? { background: isLight ? '#111827' : '#ffffff', color: isLight ? '#ffffff' : '#111827', borderColor: isLight ? '#111827' : '#ffffff' }
    : { background: 'var(--lo-bg-float)', color: 'var(--lo-text-default)', borderColor: 'var(--lo-border-neutral-l1)' };

  return (
    <div data-message-renderer className={`flex text-xs ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[86%] rounded-2xl border px-3 py-2 shadow-sm ${isError ? 'border-red-200 bg-red-50' : ''}`}
        style={isError ? undefined : shellStyle}
      >
        {!isUser && <div className="mb-0.5 font-medium" style={{ color: 'var(--lo-text-default)' }}>{message.step}</div>}
        {message.content && (
          <div data-message-text className={isUser ? '' : 'text-[color:var(--lo-text-secondary)]'}>{message.content}</div>
        )}
        {message.assets.length > 0 && (
          <div data-message-asset-list className="mt-2 grid gap-2">
            {message.assets.map((asset) => {
              if (asset.type === 'image') {
                return <img data-message-image data-message-image-thumb key={asset.url} src={asset.url} alt={message.step || 'MOYAG image result'} className="max-h-36 w-full rounded-xl object-cover" />;
              }
              if (asset.type === 'video') {
                return <video data-message-video key={asset.url} src={asset.url} controls className="max-h-44 w-full rounded-lg object-cover" />;
              }
              return <a key={asset.url} href={asset.url} className="text-[color:var(--lo-highlight)]" target="_blank" rel="noreferrer">查看素材</a>;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
