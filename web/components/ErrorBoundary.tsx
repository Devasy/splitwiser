import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCcw, Home } from 'lucide-react';
import { Button } from './ui/Button';
import { useTheme } from '../contexts/ThemeContext';
import { THEMES } from '../constants';

// --- Types ---

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// --- Fallback UI Component ---

const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error | null, resetErrorBoundary: () => void }) => {
  const { style, mode } = useTheme();
  const isNeo = style === THEMES.NEOBRUTALISM;
  const isDark = mode === 'dark';

  // Base container styles
  const containerBase = "min-h-[400px] w-full flex flex-col items-center justify-center p-8 text-center";

  // Theme-specific styles
  const neoStyles = isDark
    ? "bg-neo-dark text-white border-2 border-white shadow-[8px_8px_0px_0px_rgba(255,255,255,1)]"
    : "bg-white text-black border-2 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]";

  const glassStyles = isDark
    ? "bg-black/30 backdrop-blur-md border border-white/10 text-white shadow-xl rounded-2xl"
    : "bg-white/60 backdrop-blur-md border border-white/40 text-gray-900 shadow-xl rounded-2xl";

  const cardClasses = `max-w-md w-full ${isNeo ? neoStyles : glassStyles} p-8 transition-all duration-300`;

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4">
      <div
        role="alert"
        className={cardClasses}
      >
        <div className={`mb-6 flex justify-center`}>
          <div className={`p-4 ${isNeo ? (isDark ? 'bg-red-900' : 'bg-red-100') : 'bg-red-500/10 rounded-full'}`}>
            <AlertTriangle size={48} className="text-red-500" strokeWidth={isNeo ? 2.5 : 2} />
          </div>
        </div>

        <h2 className={`text-2xl font-bold mb-2 ${isNeo ? 'font-mono uppercase tracking-tight' : ''}`}>
          Something went wrong
        </h2>

        <p className={`mb-6 opacity-70 ${isNeo ? 'font-mono text-sm' : ''}`}>
          {error?.message || "An unexpected error occurred. Please try again."}
        </p>

        <div className="flex flex-col gap-3">
          <Button
            onClick={resetErrorBoundary}
            className="w-full justify-center"
            variant="primary"
          >
            <RefreshCcw size={18} />
            Try Again
          </Button>

          <Button
            onClick={() => window.location.href = '/'}
            variant="ghost"
            className="w-full justify-center"
          >
            <Home size={18} />
            Back to Home
          </Button>
        </div>
      </div>
    </div>
  );
};

// --- Error Boundary Class ---

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
    // Optional: Only reload if strictly necessary, but resetting state is often enough for React
    // If the error persists, the user can refresh the browser.
    // For now, let's just reset the state to try re-rendering.
    // However, if the error is in the initial render of the component tree, it might loop.
    // A safe bet for a "global" error boundary is often a full reload if simple reset fails.
    // Let's stick to state reset first.
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // We need to render the Fallback wrapped in a Theme consumer equivalent
      // Since ErrorFallback is a functional component using hooks, we can just render it.
      // But ErrorBoundary is inside ThemeProvider in App.tsx, so the context is available.
      return <ErrorFallback error={this.state.error} resetErrorBoundary={this.handleReset} />;
    }

    return this.props.children;
  }
}
