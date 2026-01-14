import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';
import { AlertTriangle, RefreshCcw } from 'lucide-react';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  const { style } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <div
        className={`
          max-w-md w-full p-8 flex flex-col items-center text-center
          ${isNeo
            ? 'bg-neo-bg border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]'
            : 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl'
          }
        `}
        role="alert"
      >
        <div className={`mb-6 p-4 rounded-full ${isNeo ? 'bg-red-500 border-2 border-black' : 'bg-red-500/20'}`}>
          <AlertTriangle size={48} className={isNeo ? 'text-white' : 'text-red-500'} />
        </div>

        <h2 className={`text-2xl font-bold mb-4 ${isNeo ? 'font-mono uppercase' : 'text-white'}`}>
          Something went wrong
        </h2>

        <p className={`mb-8 ${isNeo ? 'font-mono' : 'text-white/70'}`}>
          {error.message || "An unexpected error occurred. Please try again."}
        </p>

        <Button
          onClick={resetErrorBoundary}
          variant={isNeo ? 'primary' : 'primary'}
          className="w-full"
        >
          <RefreshCcw size={18} />
          Try Again
        </Button>
      </div>
    </div>
  );
};

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    // Optional: reload page if state reset isn't enough
    window.location.reload();
  };

  render() {
    if (this.state.hasError && this.state.error) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.handleReset} />;
    }

    return this.props.children;
  }
}
