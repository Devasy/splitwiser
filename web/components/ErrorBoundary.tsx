import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';
import { Card } from './ui/Card';

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

  const handleHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <Card className="max-w-md w-full flex flex-col items-center text-center">
        <div className={`mb-4 p-4 rounded-full ${isNeo ? 'bg-red-200 border-2 border-black' : 'bg-red-500/20'}`}>
          <AlertTriangle className={`w-12 h-12 ${isNeo ? 'text-black' : 'text-red-500'}`} aria-hidden="true" />
        </div>

        <h2 className={`text-2xl font-bold mb-2 ${isNeo ? 'uppercase' : ''}`}>
          Something went wrong
        </h2>

        <p className="opacity-70 mb-6">
          We encountered an unexpected error. Please try again.
        </p>

        {error && (
            <div
              role="alert"
              className={`w-full p-3 mb-6 text-sm text-left overflow-auto max-h-32 rounded ${
                isNeo ? 'bg-gray-100 border-2 border-black font-mono' : 'bg-black/10 font-mono'
            }`}>
                {error.message}
            </div>
        )}

        <div className="flex gap-4 w-full">
          <Button
            variant="ghost"
            onClick={handleHome}
            className="flex-1"
          >
            <Home className="w-4 h-4 mr-2" aria-hidden="true" />
            Home
          </Button>
          <Button
            variant="primary"
            onClick={resetErrorBoundary}
            className="flex-1"
          >
            <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
            Try Again
          </Button>
        </div>
      </Card>
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

  public resetErrorBoundary = () => {
    // For a top-level boundary, reloading is often the safest way to recover
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.resetErrorBoundary} />;
    }

    return this.props.children;
  }
}
