import React from 'react';
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ThemeWrapper } from './components/layout/ThemeWrapper';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import { ToastContainer } from './components/ui/Toast';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Auth } from './pages/Auth';
import { Dashboard } from './pages/Dashboard';
import { Friends } from './pages/Friends';
import { GroupDetails } from './pages/GroupDetails';
import { Groups } from './pages/Groups';
import { Profile } from './pages/Profile';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactElement }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <div className="h-screen w-full flex items-center justify-center">Loading...</div>;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

const AppRoutes = () => {
    const { isAuthenticated } = useAuth();
    
    return (
        <Routes>
          <Route path="/login" element={!isAuthenticated ? <ThemeWrapper><Auth /></ThemeWrapper> : <Navigate to="/dashboard" />} />
          <Route path="/signup" element={!isAuthenticated ? <ThemeWrapper><Auth /></ThemeWrapper> : <Navigate to="/dashboard" />} />
          
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/groups" element={<ProtectedRoute><Groups /></ProtectedRoute>} />
          <Route path="/groups/:id" element={<ProtectedRoute><GroupDetails /></ProtectedRoute>} />
          <Route path="/friends" element={<ProtectedRoute><Friends /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
        </Routes>
    );
}

const App = () => {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <HashRouter>
              <ErrorBoundary>
                <AppRoutes />
              </ErrorBoundary>
              <ToastContainer />
          </HashRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
};

export default App;