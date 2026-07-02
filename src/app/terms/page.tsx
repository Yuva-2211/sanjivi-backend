import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-brand-bg px-6 py-16 text-brand-text">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="text-xs font-bold text-primary hover:underline">Back to Sanjivi AI</Link>
        <h1 className="mt-8 text-4xl font-black font-serif">Terms of Service</h1>
        <p className="mt-4 text-sm text-brand-muted leading-relaxed">
          By using Sanjivi AI, you agree to use it for educational wellness information only. The service does not provide diagnosis, treatment, prescriptions, or emergency medical care.
        </p>
        <h2 className="mt-8 text-lg font-bold">User responsibility</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          You are responsible for consulting qualified professionals before acting on health information, especially if you are pregnant, elderly, immunocompromised, taking medication, or managing a diagnosed condition.
        </p>
        <h2 className="mt-8 text-lg font-bold">Service availability</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          Early access features may change, pause, or be removed as the product develops.
        </p>
      </div>
    </main>
  );
}
