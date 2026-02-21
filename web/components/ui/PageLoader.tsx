import React from 'react';
import { Spinner } from './Spinner';

export const PageLoader = () => {
  return (
    <div className="h-screen w-full flex items-center justify-center">
      <Spinner size={48} className="text-emerald-500 dark:text-emerald-400" />
    </div>
  );
};
