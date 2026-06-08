import { Component } from 'react';
import type { ReactNode } from 'react';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: string; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: '' };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="liquid-page min-h-screen flex items-center justify-center">
          <div className="liquid-card p-8 max-w-md text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <h2 className="text-lg font-medium text-gray-100">页面出错了</h2>
            <p className="text-sm text-gray-500">{this.state.error}</p>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-400 rounded-lg text-sm"
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
