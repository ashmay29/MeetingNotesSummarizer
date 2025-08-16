import * as React from 'react';

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className = '', ...props }, ref) => {
  const base = 'w-full rounded-lg border border-white/20 bg-white/10 text-white placeholder-white/60 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400/70';
  return <textarea ref={ref} className={[base, className].join(' ')} {...props} />;
});
Textarea.displayName = 'Textarea';
