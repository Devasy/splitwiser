import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen w-full flex items-center justify-center p-4">
           <ErrorFallback error={this.state.error} onRetry={this.handleRetry} />
        </div>
      );
    }

    return this.props.children;
  }
}

const ErrorFallback = ({ error, onRetry }: { error: Error | null, onRetry: () => void }) => {
    return (
        <Card className="max-w-md w-full text-center" title="Something went wrong">
            <div className="flex flex-col items-center gap-4 py-4">
                <div className="p-3 rounded-full bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">
                    <AlertTriangle size={32} />
                </div>

                <p className="text-gray-600 dark:text-gray-300">
                    {error?.message || 'An unexpected error occurred while rendering this page.'}
                </p>

                <Button
                    variant="primary"
                    onClick={onRetry}
                    className="w-full flex items-center justify-center gap-2"
                >
                    <RefreshCw size={18} />
                    Reload Page
                </Button>
            </div>
        </Card>
    );
};
