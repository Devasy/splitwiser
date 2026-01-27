import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';

// Functional component for the UI to use hooks like useTheme
const ErrorFallback: React.FC<{
  error: Error | null;
  resetErrorBoundary: () => void;
}> = ({ error, resetErrorBoundary }) => {
  // style is used by Card internally, we don't need it here unless we have specific styles

  return (
    <div className="min-h-[50vh] flex items-center justify-center p-4">
      <Card className="max-w-md w-full flex flex-col items-center text-center">
        <div className="bg-red-100 p-4 rounded-full mb-4 text-red-600">
          <AlertTriangle size={48} strokeWidth={1.5} />
        </div>

        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>

        <p className="text-gray-500 mb-6 dark:text-gray-400">
          {error?.message || "An unexpected error occurred. Please try again."}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
          <Button
            variant="primary"
            onClick={resetErrorBoundary}
            className="flex-1"
          >
            <RefreshCw size={18} className="mr-2" />
            Try Again
          </Button>

          <Button
            variant="ghost"
            onClick={() => window.location.reload()}
            className="flex-1"
          >
            <Home size={18} className="mr-2" />
            Back to Home
          </Button>
        </div>
      </Card>
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
    console.error('ErrorBoundary caught an error:', error, errorInfo);
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
