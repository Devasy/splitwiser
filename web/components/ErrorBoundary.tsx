import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

const ErrorFallback: React.FC<{ error: Error | null, resetErrorBoundary: () => void }> = ({ error, resetErrorBoundary }) => {
  const { style, mode } = useTheme();

  const isNeo = style === THEMES.NEOBRUTALISM;
  const isDark = mode === 'dark';

  // Base container styles
  const containerClasses = `min-h-screen w-full flex items-center justify-center p-4 transition-colors duration-300
    ${isNeo
      ? (isDark ? 'bg-zinc-900' : 'bg-yellow-50')
      : (isDark ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-black' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50')
    }`;

  // Card styles
  const cardClasses = `max-w-md w-full p-8 transition-all duration-300
    ${isNeo
      ? `border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] ${isDark ? 'bg-zinc-800 text-white' : 'bg-white text-black'} rounded-none`
      : `backdrop-blur-xl border border-white/20 shadow-2xl rounded-2xl ${isDark ? 'bg-white/5 text-white' : 'bg-white/70 text-gray-800'}`
    }`;

  // Text styles
  const titleClasses = `text-3xl font-bold mb-4 ${isNeo ? 'uppercase tracking-tighter' : 'tracking-tight'}`;
  const messageClasses = `text-lg mb-6 opacity-80 ${isNeo ? 'font-mono text-sm' : ''}`;
  const codeClasses = `p-4 mb-8 rounded text-sm font-mono overflow-auto
    ${isNeo
      ? 'border border-black bg-gray-100 text-black'
      : (isDark ? 'bg-black/30 text-red-300' : 'bg-red-50 text-red-600')
    }`;

  return (
    <div className={containerClasses}>
      <div
        role="alert"
        className={cardClasses}
        aria-labelledby="error-title"
        aria-describedby="error-desc"
      >
        <div className="flex flex-col items-center text-center">
          <div className={`mb-6 p-4 rounded-full ${isNeo ? 'bg-red-500 border-2 border-black' : 'bg-red-500/10'}`}>
            <AlertTriangle className={`w-12 h-12 ${isNeo ? 'text-white' : 'text-red-500'}`} aria-hidden="true" />
          </div>

          <h1 id="error-title" className={titleClasses}>
            Something went wrong
          </h1>

          <p id="error-desc" className={messageClasses}>
            We encountered an unexpected error. Please try again or return to the dashboard.
          </p>

          {error && (
            <div className={codeClasses}>
              {error.message}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 w-full justify-center">
            <Button
              onClick={resetErrorBoundary}
              variant="primary"
              className="w-full sm:w-auto"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </Button>

            <Button
              onClick={() => window.location.href = window.location.origin}
              variant="secondary"
              className="w-full sm:w-auto"
            >
              <Home className="w-4 h-4" />
              Back to Home
            </Button>
          </div>
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

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    // Here you would typically log to a service like Sentry
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    // Reloading the page is often the safest "retry" for client-side errors
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.handleReset} />;
    }

    return this.props.children;
  }
}
