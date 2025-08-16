type ToastOpts = { title?: string; description?: string; variant?: 'default' | 'destructive' };

export function useToast() {
  function toast({ title, description, variant }: ToastOpts) {
    const prefix = variant === 'destructive' ? '❌ ' : '✅ ';
    if (title) {
      // eslint-disable-next-line no-console
      console.log(prefix + title + (description ? ` — ${description}` : ''));
    }
    if (typeof window !== 'undefined') {
      // lightweight fallback
      const msg = [title, description].filter(Boolean).join('\n');
      if (msg) window.setTimeout(() => alert(msg), 0);
    }
  }
  return { toast };
}
