import React, { ErrorInfo, ReactNode } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundaryInner extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={() => this.setState({ hasError: false, error: null })} />;
    }

    return this.props.children;
  }
}

const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
    return (
        <div className="min-h-screen w-full flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900 transition-colors">
             <Card className="max-w-md w-full" title="Something went wrong">
                <div className="flex flex-col items-center gap-6 text-center py-4">
                    <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-full">
                        <AlertTriangle size={48} />
                    </div>

                    <div className="space-y-2">
                        <h3 className="text-lg font-semibold">Application Error</h3>
                        <p className="text-sm opacity-70 font-mono bg-gray-100 dark:bg-black/30 p-3 rounded text-left overflow-auto max-h-32 text-xs">
                            {error?.message || "An unexpected error occurred."}
                        </p>
                    </div>

                    <div className="flex gap-3 w-full mt-2">
                        <Button
                            variant="secondary"
                            className="flex-1"
                            onClick={() => window.location.href = window.location.origin}
                        >
                            <Home size={18} /> Home
                        </Button>
                        <Button
                            variant="primary"
                            className="flex-1"
                            onClick={resetErrorBoundary}
                        >
                             <RefreshCw size={18} /> Retry
                        </Button>
                    </div>
                </div>
             </Card>
        </div>
    )
}

export const ErrorBoundary = ErrorBoundaryInner;
