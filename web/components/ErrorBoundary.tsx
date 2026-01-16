import React, { Component, ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface ErrorFallbackProps {
  error: Error | null;
  resetError: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetError }) => {
  const { style, mode } = useTheme();

  const isNeo = style === THEMES.NEOBRUTALISM;
  const isDark = mode === 'dark';

  let containerClasses = "";
  if (isNeo) {
    containerClasses = `border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-white ${isDark ? 'bg-zinc-800 text-white' : 'text-black'}`;
  } else {
    containerClasses = `rounded-2xl border border-white/10 shadow-2xl backdrop-blur-xl ${isDark ? 'bg-black/60 text-white' : 'bg-white/60 text-gray-900'}`;
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className={`w-full max-w-md p-8 text-center ${containerClasses}`}>
        <div className={`mb-6 flex justify-center`}>
          <div className={`p-4 rounded-full ${isNeo ? 'border-2 border-black bg-neo-second' : 'bg-red-500/20 text-red-500'}`}>
            <AlertTriangle size={48} className={isNeo ? 'text-black' : ''} />
          </div>
        </div>

        <h2 className={`text-2xl font-bold mb-2 ${isNeo ? 'uppercase font-mono tracking-wider' : ''}`}>
          Something went wrong
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          {error?.message || "An unexpected error occurred. We're sorry for the inconvenience."}
        </p>

        <div className="flex flex-col gap-3">
          <Button onClick={resetError} className="w-full">
            <RefreshCw size={18} />
            Try Again
          </Button>

          <Button
            variant="ghost"
            onClick={() => window.location.href = '/'}
            className="w-full"
          >
            <Home size={18} />
            Back to Home
          </Button>
        </div>
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

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}
