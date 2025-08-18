export default function LoadingMeetingPage() {
  return (
    <div className="grid gap-8">
      <section className="card p-6 md:p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-24 bg-white/10 rounded" />
          <div className="h-8 w-64 bg-white/10 rounded" />
          <div className="h-4 w-full bg-white/10 rounded" />
          <div className="h-4 w-11/12 bg-white/10 rounded" />
          <div className="h-4 w-10/12 bg-white/10 rounded" />
          <div className="h-64 w-full bg-white/10 rounded" />
        </div>
      </section>
    </div>
  );
}
