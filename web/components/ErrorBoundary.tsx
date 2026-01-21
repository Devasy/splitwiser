import React, { Component, ErrorInfo } from 'react';
import { ThemeWrapper } from './layout/ThemeWrapper';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
  const isDev = import.meta.env.DEV;

  return (
    <ThemeWrapper>
      <div className="flex items-center justify-center min-h-screen p-4">
        <Card className="max-w-md w-full" title="Something went wrong">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="p-3 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
              <AlertTriangle size={32} />
            </div>

            <p className="text-gray-600 dark:text-gray-300">
              We encountered an unexpected error. Please try again.
            </p>

            {isDev && error && (
              <div className="w-full p-2 mt-2 text-xs text-left font-mono bg-black/5 dark:bg-white/5 rounded overflow-auto max-h-32 border border-gray-200 dark:border-gray-700">
                {error.toString()}
              </div>
            )}

            <div className="flex gap-3 w-full mt-4">
              <Button
                variant="primary"
                className="flex-1 flex items-center justify-center gap-2"
                onClick={resetErrorBoundary}
              >
                <RefreshCw size={16} />
                Try Again
              </Button>
              <Button
                variant="secondary"
                className="flex-1 flex items-center justify-center gap-2"
                onClick={() => window.location.href = '/'}
              >
                <Home size={16} />
                Home
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </ThemeWrapper>
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

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.handleReset} />;
    }

    return this.props.children;
  }
}
