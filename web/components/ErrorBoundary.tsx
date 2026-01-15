import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

const ErrorFallback = ({ error, resetErrorBoundary }: { error?: Error, resetErrorBoundary: () => void }) => {
  const { style, mode } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;
  const isDark = mode === 'dark';

  return (
    <div className={`min-h-[500px] w-full flex flex-col items-center justify-center p-6 text-center
      ${isNeo ? 'bg-neo-bg text-black' : isDark ? 'text-white' : 'text-gray-900'}
    `}>
      <div className={`
        max-w-md w-full p-8 flex flex-col items-center gap-6
        ${isNeo
          ? 'bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]'
          : `backdrop-blur-xl border ${isDark ? 'bg-white/10 border-white/20' : 'bg-white/70 border-white/40'} rounded-2xl shadow-xl`
        }
      `}>
        <div className={`
          p-4 rounded-full flex items-center justify-center
          ${isNeo
            ? 'bg-red-400 border-2 border-black'
            : 'bg-red-500/20 text-red-500'
          }
        `}>
          <AlertTriangle size={48} className={isNeo ? 'text-black' : 'currentColor'} aria-hidden="true" />
        </div>

        <div className="space-y-3">
          <h2 className="text-2xl font-bold" role="alert">Something went wrong</h2>
          <p className={`${isNeo ? 'text-gray-700' : isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            We encountered an unexpected error. Please try reloading the page.
          </p>

          {import.meta.env.DEV && error && (
            <div className="mt-4 w-full">
              <p className="text-xs font-mono text-left mb-1 opacity-70">Error details:</p>
              <pre className={`
                p-3 text-xs text-left overflow-auto max-h-40 w-full rounded
                ${isNeo ? 'bg-gray-100 border border-black text-black' : 'bg-black/30 text-white/90'}
              `}>
                {error.message}
              </pre>
            </div>
          )}
        </div>

        <Button
          onClick={resetErrorBoundary}
          variant="primary"
          className="w-full flex items-center justify-center gap-2 mt-2"
        >
          <RefreshCw size={18} aria-hidden="true" />
          Reload Page
        </Button>
      </div>
    </div>
  );
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  resetErrorBoundary = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.resetErrorBoundary} />;
    }

    return this.props.children;
  }
}
