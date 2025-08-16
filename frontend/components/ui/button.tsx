import * as React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'default' | 'outline';
  size?: 'sm' | 'md' | 'lg';
};

const base = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400/70 disabled:opacity-60 disabled:pointer-events-none';
const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-11 px-5 text-base',
};
const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
  default: 'bg-indigo-600 text-white hover:bg-indigo-500',
  outline: 'border border-white/20 bg-transparent text-white hover:bg-white/10',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'default', size = 'md', ...props }, ref) => (
    <button ref={ref} className={[base, sizes[size], variants[variant], className].join(' ')} {...props} />
  )
);
Button.displayName = 'Button';
