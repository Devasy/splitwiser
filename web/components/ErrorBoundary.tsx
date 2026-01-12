import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';
import { useNavigate } from 'react-router-dom';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

// Functional component to access hooks
const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
  const { style } = useTheme();
  const navigate = useNavigate();

  const isNeo = style === THEMES.NEOBRUTALISM;

  const handleHome = () => {
    resetErrorBoundary();
    navigate('/');
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <Card className="max-w-md w-full text-center">
        <div className="flex flex-col items-center gap-4">
          <div className={`p-4 rounded-full ${isNeo ? 'bg-red-100 border-2 border-black' : 'bg-red-500/10'}`}>
            <AlertTriangle size={48} className="text-red-500" aria-hidden="true" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold" role="alert">Something went wrong</h2>
            <p className="text-sm opacity-80 break-words max-h-32 overflow-y-auto">
              {error?.message || "An unexpected error occurred."}
            </p>
          </div>

          <div className="flex gap-3 mt-4 w-full justify-center">
            <Button variant="ghost" onClick={handleHome} className="flex-1">
              <Home size={18} />
              Home
            </Button>
            <Button variant="primary" onClick={resetErrorBoundary} className="flex-1">
              <RefreshCw size={18} />
              Retry
            </Button>
          </div>
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
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.resetErrorBoundary} />;
    }

    return this.props.children;
  }
}
