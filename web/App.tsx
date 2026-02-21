import React, { Suspense } from 'react';
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ThemeWrapper } from './components/layout/ThemeWrapper';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ToastProvider } from './contexts/ToastContext';
import { ConfirmProvider } from './contexts/ConfirmContext';
import { ToastContainer } from './components/ui/Toast';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PageLoader } from './components/ui/PageLoader';

// Lazy load pages
const Auth = React.lazy(() => import('./pages/Auth').then(module => ({ default: module.Auth })));
const Dashboard = React.lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const Friends = React.lazy(() => import('./pages/Friends').then(module => ({ default: module.Friends })));
const GroupDetails = React.lazy(() => import('./pages/GroupDetails').then(module => ({ default: module.GroupDetails })));
const Groups = React.lazy(() => import('./pages/Groups').then(module => ({ default: module.Groups })));
const Profile = React.lazy(() => import('./pages/Profile').then(module => ({ default: module.Profile })));
const SplitwiseCallback = React.lazy(() => import('./pages/SplitwiseCallback').then(module => ({ default: module.SplitwiseCallback })));
const SplitwiseGroupSelection = React.lazy(() => import('./pages/SplitwiseGroupSelection').then(module => ({ default: module.SplitwiseGroupSelection })));
const SplitwiseImport = React.lazy(() => import('./pages/SplitwiseImport').then(module => ({ default: module.SplitwiseImport })));

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactElement }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <PageLoader />;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

const AppRoutes = () => {
    const { isAuthenticated } = useAuth();
    
    return (
        <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/login" element={!isAuthenticated ? <ThemeWrapper><Auth /></ThemeWrapper> : <Navigate to="/dashboard" />} />
              <Route path="/signup" element={!isAuthenticated ? <ThemeWrapper><Auth /></ThemeWrapper> : <Navigate to="/dashboard" />} />

              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/groups" element={<ProtectedRoute><Groups /></ProtectedRoute>} />
              <Route path="/groups/:id" element={<ProtectedRoute><GroupDetails /></ProtectedRoute>} />
              <Route path="/friends" element={<ProtectedRoute><Friends /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/import/splitwise" element={<ProtectedRoute><SplitwiseImport /></ProtectedRoute>} />
              <Route path="/import/splitwise/select-groups" element={<ProtectedRoute><SplitwiseGroupSelection /></ProtectedRoute>} />
              <Route path="/import/splitwise/callback" element={<ProtectedRoute><SplitwiseCallback /></ProtectedRoute>} />

              <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
            </Routes>
        </Suspense>
    );
}

const App = () => {
  return (
    <ThemeProvider>
      <ToastProvider>
        <ConfirmProvider>
          <AuthProvider>
            <HashRouter>
                <ErrorBoundary>
                  <AppRoutes />
                </ErrorBoundary>
                <ToastContainer />
            </HashRouter>
          </AuthProvider>
        </ConfirmProvider>
      </ToastProvider>
    </ThemeProvider>
  );
};

export default App;