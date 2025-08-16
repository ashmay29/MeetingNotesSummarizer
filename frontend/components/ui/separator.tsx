import * as React from 'react';

export function Separator({ className = '', ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={["h-px w-full bg-white/10", className].join(' ')} {...props} />;
}
