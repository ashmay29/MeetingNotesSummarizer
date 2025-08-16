import * as React from 'react';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className = '', ...props }, ref) => {
  const base = 'w-full h-10 rounded-lg border border-white/20 bg-white/10 text-white placeholder-white/60 px-3 focus:outline-none focus:ring-2 focus:ring-indigo-400/70';
  return <input ref={ref} className={[base, className].join(' ')} {...props} />;
});
Input.displayName = 'Input';
