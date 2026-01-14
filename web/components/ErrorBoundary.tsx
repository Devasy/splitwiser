import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

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

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <Card className="max-w-md w-full text-center">
        <div className={`flex justify-center mb-6 ${isNeo ? 'text-black' : 'text-red-400'}`}>
          <AlertTriangle size={64} strokeWidth={isNeo ? 2.5 : 1.5} />
        </div>

        <h2 className={`text-2xl font-bold mb-4 ${isNeo ? 'uppercase font-mono' : ''}`}>
          Something went wrong
        </h2>

        <div className={`p-4 mb-6 rounded text-sm text-left overflow-auto max-h-32 ${
          isNeo
            ? 'bg-red-100 border-2 border-black text-black font-mono'
            : 'bg-red-500/10 border border-red-500/20 text-red-200'
        }`}>
          {error?.message || "An unexpected error occurred."}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button
            onClick={resetErrorBoundary}
            variant="primary"
            className="w-full sm:w-auto"
          >
            <RefreshCw size={18} />
            Try Again
          </Button>

          <Button
            onClick={() => window.location.reload()}
            variant="ghost"
            className="w-full sm:w-auto"
          >
            <Home size={18} />
            Reload Page
          </Button>
        </div>
      </Card>
    </div>
  );
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  resetErrorBoundary = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          resetErrorBoundary={this.resetErrorBoundary}
        />
      );
    }

    return this.props.children;
  }
}
