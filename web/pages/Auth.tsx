import { AnimatePresence, motion } from 'framer-motion';
import { ArrowRight, CreditCard, Sparkles } from 'lucide-react';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Spinner } from '../components/ui/Spinner';
import { THEMES } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../contexts/ToastContext';
import {
  login as apiLogin,
  signup as apiSignup,
  loginWithGoogle,
} from '../services/api';
import { signInWithGoogle } from '../services/firebase';

export const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const { style, toggleStyle } = useTheme();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      const idToken = await signInWithGoogle();
      const res = await loginWithGoogle(idToken);
      const { access_token, user } = res.data ?? {};
      if (!access_token || !user) {
        throw new Error('Invalid response from server');
      }
      login(access_token, user);
      addToast('Welcome back!', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Google login error:', err);
      if (err.code === 'auth/popup-closed-by-user') {
        setError('');
      } else if (err.response) {
        const detail = err.response.data?.detail;
        setError(
          typeof detail === 'string'
            ? detail
            : detail?.[0]?.msg || 'Google authentication failed'
        );
      } else {
        setError(err.message || 'Google authentication failed. Please try again.');
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let res;
      if (isLogin) {
        res = await apiLogin({ email, password });
      } else {
        res = await apiSignup({ email, password, name });
      }

      const { access_token, user } = res.data;
      login(access_token, user);
      addToast(isLogin ? 'Welcome back!' : 'Account created successfully!', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response) {
        const detail = err.response.data?.detail;
        setError(
          typeof detail === 'string'
            ? detail
            : detail?.[0]?.msg || 'Authentication failed'
        );
      } else {
        setError('Something went wrong');
      }
    } finally {
      setLoading(false);
    }
  };

  const isNeo = style === THEMES.NEOBRUTALISM;

  return (
    <div className="min-h-screen w-full flex">
      {/* Left Side - Visuals */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-black text-white items-center justify-center p-12">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-purple-900 opacity-50" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20" />

        {/* Animated Shapes */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
          className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-blue-500/30 to-purple-500/30 blur-3xl rounded-full"
        />

        <div className="relative z-10 max-w-lg">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="flex items-center gap-4 mb-8">
              <div className={`w-16 h-16 bg-white text-black flex items-center justify-center ${isNeo ? 'rounded-none border-4 border-white shadow-[8px_8px_0px_0px_rgba(255,255,255,0.5)]' : 'rounded-2xl shadow-2xl'}`}>
                <CreditCard size={32} strokeWidth={2.5} />
              </div>
              <h1 className={`text-5xl font-black tracking-tighter ${isNeo ? 'font-mono uppercase' : ''}`}>Splitwiser</h1>
            </div>
            <h2 className={`text-3xl font-bold mb-6 leading-tight ${isNeo ? 'font-mono' : ''}`}>
              The smartest way to share expenses with friends.
            </h2>
            <div className="space-y-4 text-lg opacity-70">
              <p className="flex items-center gap-3">
                <span className={`w-6 h-6 flex items-center justify-center text-green-400 ${isNeo ? 'bg-green-900 rounded-none' : 'bg-green-500/20 rounded-full'}`}>✓</span>
                Track shared expenses effortlessly
              </p>
              <p className="flex items-center gap-3">
                <span className={`w-6 h-6 flex items-center justify-center text-blue-400 ${isNeo ? 'bg-blue-900 rounded-none' : 'bg-blue-500/20 rounded-full'}`}>✓</span>
                Settle up with a single tap
              </p>
              <p className="flex items-center gap-3">
                <span className={`w-6 h-6 flex items-center justify-center text-purple-400 ${isNeo ? 'bg-purple-900 rounded-none' : 'bg-purple-500/20 rounded-full'}`}>✓</span>
                Beautiful, intuitive interface
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-6 sm:p-12 relative">
        <div className="absolute top-6 right-6">
          <Button variant="ghost" size="sm" onClick={toggleStyle} className="gap-2">
            <Sparkles size={16} />
            {isNeo ? 'Switch to Glass' : 'Switch to Neo'}
          </Button>
        </div>

        <div className="w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <h2 className={`text-3xl font-black tracking-tight ${isNeo ? 'font-mono uppercase' : ''}`}>
              {isLogin ? 'Welcome back' : 'Create an account'}
            </h2>
            <p className="mt-2 text-sm opacity-60">
              {isLogin ? 'Enter your details to access your account' : 'Start splitting bills in seconds'}
            </p>
          </div>

          <div className="space-y-4">
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={googleLoading}
              className={`w-full flex items-center justify-center gap-3 p-3 font-bold transition-all ${isNeo
                ? 'bg-white border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] rounded-none'
                : 'bg-white text-black hover:bg-gray-50 border border-gray-200 shadow-sm rounded-xl'
                }`}
            >
              {googleLoading ? (
                <Spinner
                  size={20}
                  className={isNeo ? 'text-black' : 'text-gray-600'}
                  ariaLabel="Signing in with Google"
                />
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 24 24" role="img" aria-labelledby="google-logo-title">
                  <title id="google-logo-title">Google logo</title>
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
              )}
              <span>Continue with Google</span>
            </button>

            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
              <span className="flex-shrink-0 mx-4 text-xs font-bold opacity-50 uppercase">Or continue with email</span>
              <div className="flex-grow border-t border-gray-200 dark:border-gray-700"></div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <AnimatePresence mode="wait">
                {!isLogin && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                  >
                    <Input
                      placeholder="Full Name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className={isNeo ? 'rounded-none' : ''}
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              <Input
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className={isNeo ? 'rounded-none' : ''}
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className={isNeo ? 'rounded-none' : ''}
              />

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`p-3 text-red-600 text-sm font-medium border border-red-100 ${isNeo ? 'bg-red-100 border-2 border-black rounded-none' : 'bg-red-50 rounded-lg'}`}
                >
                  {error}
                </motion.div>
              )}

              <Button
                type="submit"
                isLoading={loading}
                className={`w-full py-4 text-lg ${isNeo ? 'rounded-none' : ''}`}
              >
                {isLogin ? 'Log In' : 'Create Account'} <ArrowRight size={20} />
              </Button>
            </form>

            <div className="text-center pt-4">
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                className="text-sm font-bold hover:underline opacity-70 hover:opacity-100 transition-opacity"
              >
                {isLogin
                  ? "Don't have an account? Sign Up"
                  : 'Already have an account? Log In'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
