import React, { Component, ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { Button } from './ui/Button';
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

  const handleReload = () => {
    window.location.reload();
  };

  const handleHome = () => {
    window.location.href = '/';
  };

  return (
    <div className={`min-h-[80vh] w-full flex flex-col items-center justify-center p-6 text-center`}>
      <div className={`p-8 max-w-lg w-full ${
        isNeo
          ? 'bg-white border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]'
          : 'bg-white/10 backdrop-blur-md border border-white/20 shadow-2xl rounded-2xl'
      }`}>
        <div className="flex justify-center mb-6">
          <div className={`p-4 rounded-full ${
            isNeo ? 'bg-neo-second text-black border-2 border-black' : 'bg-red-500/20 text-red-200'
          }`}>
            <AlertTriangle size={48} />
          </div>
        </div>

        <h2 className={`text-3xl font-bold mb-3 ${isNeo ? 'font-mono uppercase' : 'font-sans text-white'}`}>
          Whoops!
        </h2>

        <p className={`mb-8 ${isNeo ? 'font-mono text-base' : 'text-white/70'}`}>
          {error?.message || "Something went wrong while displaying this page. Try reloading or going back to home."}
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button onClick={handleReload} variant="primary">
            <RefreshCw size={18} />
            Try Again
          </Button>
          <Button onClick={handleHome} variant="secondary">
            <Home size={18} />
            Back to Home
          </Button>
        </div>
      </div>
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

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          resetErrorBoundary={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}
