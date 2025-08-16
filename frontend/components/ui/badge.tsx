import * as React from 'react';

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: 'default' | 'secondary' | 'outline' | 'destructive';
};

const variants: Record<NonNullable<BadgeProps['variant']>, string> = {
  default: 'bg-indigo-600 text-white',
  secondary: 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white',
  outline: 'border border-white/20 text-white',
  destructive: 'bg-red-500 text-white',
};

export function Badge({ className = '', variant = 'default', ...props }: BadgeProps) {
  const base = 'inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs';
  return <span className={[base, variants[variant], className].join(' ')} {...props} />;
}
