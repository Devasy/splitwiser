import React, { Component, ReactNode } from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import { THEMES } from '../constants';
import { useTheme } from '../contexts/ThemeContext';
import { Button } from './ui/Button';
import { ThemeWrapper } from './layout/ThemeWrapper';

// Functional component for the UI to use hooks
const ErrorFallback = () => {
  const { style } = useTheme();

  const handleRetry = () => {
    window.location.reload();
  };

  const handleHome = () => {
    window.location.href = '/';
  };

  const isNeo = style === THEMES.NEOBRUTALISM;

  return (
    <ThemeWrapper>
      <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
        <div className={`mb-6 p-4 rounded-full ${isNeo ? 'bg-neo-main border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-red-500/10 text-red-500 backdrop-blur-md border border-red-500/20'}`}>
          <AlertTriangle size={48} className={isNeo ? 'text-white' : ''} />
        </div>

        <h2 className={`text-2xl font-bold mb-2 ${isNeo ? 'font-mono uppercase' : ''}`}>
          Something went wrong
        </h2>

        <p className="text-gray-500 mb-8 max-w-md">
          We encountered an unexpected error. Please try refreshing the page or go back to home.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button onClick={handleRetry} variant="primary">
            <RefreshCw size={18} />
            Retry
          </Button>
          <Button onClick={handleHome} variant="secondary">
            <Home size={18} />
            Back to Home
          </Button>
        </div>
      </div>
    </ThemeWrapper>
  );
};

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }

    return this.props.children;
  }
}
