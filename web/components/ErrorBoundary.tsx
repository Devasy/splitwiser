import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const ErrorFallback: React.FC<{ error: Error | null; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary
}) => {
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  return (
    <div className="min-h-[50vh] w-full flex items-center justify-center p-4">
      <div
        className={`
          max-w-md w-full p-8 text-center flex flex-col items-center gap-6
          ${isNeo
            ? 'bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]'
            : 'bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-xl'
          }
        `}
      >
        <div className={`
          p-4 rounded-full
          ${isNeo ? 'bg-neo-second border-2 border-black' : 'bg-red-500/20 text-red-200'}
        `}>
          <AlertTriangle size={48} className={isNeo ? 'text-black' : 'text-red-400'} />
        </div>

        <div className="space-y-2">
          <h2 className={`text-2xl font-bold ${isNeo ? 'font-black uppercase' : 'text-white'}`}>
            Something went wrong
          </h2>
          <p className={isNeo ? 'text-black font-medium' : 'text-gray-300'}>
            We encountered an unexpected error. Try reloading the page to get back on track.
          </p>
        </div>

        {error && process.env.NODE_ENV === 'development' && (
          <div className="w-full text-left p-4 bg-black/5 rounded text-xs font-mono overflow-auto max-h-32">
            {error.toString()}
          </div>
        )}

        <Button
          onClick={resetErrorBoundary}
          variant="primary"
          className="w-full"
        >
          <RefreshCw size={18} />
          Reload Application
        </Button>
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
          resetErrorBoundary={() => window.location.reload()}
        />
      );
    }

    return this.props.children;
  }
}
