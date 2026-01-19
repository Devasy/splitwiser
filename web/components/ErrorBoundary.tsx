import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

// Functional component for the fallback UI to use Hooks
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
  const { style } = useTheme();

  const isNeo = style === THEMES.NEOBRUTALISM;

  const handleHome = () => {
    window.location.href = window.location.origin;
  };

  const containerClasses = isNeo
    ? "bg-neo-bg border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]"
    : "bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl";

  const textClasses = isNeo
    ? "text-black font-mono"
    : "text-white";

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-6 text-center">
      <div className={`p-8 rounded-xl max-w-md w-full flex flex-col items-center gap-6 ${containerClasses}`}>
        <div className={`p-4 rounded-full ${isNeo ? 'bg-red-400 border-2 border-black' : 'bg-red-500/20'}`}>
          <AlertTriangle size={48} className={isNeo ? "text-black" : "text-red-200"} />
        </div>

        <div className="space-y-2">
          <h2 className={`text-2xl font-bold ${textClasses}`}>
            Something went wrong
          </h2>
          <p className={isNeo ? "text-gray-800 font-mono text-sm" : "text-gray-200"}>
            We encountered an unexpected error.
          </p>
          {error && (
            <div className={`mt-4 p-3 text-left overflow-auto max-h-32 text-xs rounded ${isNeo ? 'bg-gray-200 border border-black' : 'bg-black/30 text-red-200 font-mono'}`}>
              {error.message}
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <Button
            onClick={resetErrorBoundary}
            variant="primary"
            className="flex-1"
          >
            <RefreshCw size={18} />
            Try Again
          </Button>
          <Button
            onClick={handleHome}
            variant="secondary"
            className="flex-1"
          >
            <Home size={18} />
            Back to Home
          </Button>
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
    console.error("Uncaught error:", error, errorInfo);
  }

  public resetErrorBoundary = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload(); // Hard reload to ensure clean state
  };

  public render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.resetErrorBoundary} />;
    }

    return this.props.children;
  }
}
