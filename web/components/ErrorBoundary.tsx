import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { Button } from './ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  const containerClass = isNeo
    ? 'bg-neo-bg text-black'
    : 'bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 text-white';

  const cardClass = isNeo
    ? 'bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-8 max-w-md w-full'
    : 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl p-8 max-w-md w-full';

  return (
    <div className={`min-h-screen w-full flex items-center justify-center p-4 ${containerClass}`}>
      <div className={cardClass}>
        <div className="flex flex-col items-center text-center gap-6">
          <div className={`p-4 rounded-full ${isNeo ? 'bg-red-200 border-2 border-black' : 'bg-red-500/20'}`}>
            <AlertTriangle size={48} className={isNeo ? 'text-black' : 'text-red-400'} />
          </div>

          <div className="space-y-2">
            <h1 className={`text-2xl font-bold ${isNeo ? 'uppercase tracking-wide' : ''}`}>
              Something went wrong
            </h1>
            <p className={isNeo ? 'text-gray-800' : 'text-gray-300'}>
              We encountered an unexpected error. Our team has been notified.
            </p>
            {error && (
              <div className={`mt-4 p-3 text-sm font-mono text-left overflow-auto max-h-32 ${
                isNeo ? 'bg-gray-100 border-2 border-black' : 'bg-black/30 rounded-lg text-red-300'
              }`}>
                {error.message}
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-4 w-full pt-2">
            <Button
              onClick={resetErrorBoundary}
              className="flex-1"
              variant="primary"
            >
              <RefreshCw size={18} />
              Try Again
            </Button>
            <Button
              onClick={() => window.location.href = window.location.origin}
              className="flex-1"
              variant="secondary"
            >
              <Home size={18} />
              Back to Home
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          resetErrorBoundary={() => {
            this.setState({ hasError: false, error: null });
            window.location.reload();
          }}
        />
      );
    }

    return this.props.children;
  }
}
