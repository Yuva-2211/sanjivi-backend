import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-brand-bg px-6 py-16 text-brand-text">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="text-xs font-bold text-primary hover:underline">Back to Sanjivi AI</Link>
        <h1 className="mt-8 text-4xl font-black font-serif">Privacy Policy</h1>
        <p className="mt-4 text-sm text-brand-muted leading-relaxed">
          Sanjivi AI collects information you submit, such as early access names, emails, chat messages, and optional health context, to provide educational wellness responses and product updates.
        </p>
        <h2 className="mt-8 text-lg font-bold">How we use data</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          We use submitted data to operate the service, improve safety checks, respond to support requests, and contact early access users. We do not sell personal or diagnostic data.
        </p>
        <h2 className="mt-8 text-lg font-bold">Health information</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          Health queries may include sensitive information. Use Sanjivi AI only for educational guidance, and avoid submitting information you do not want processed by the service.
        </p>
        <h2 className="mt-8 text-lg font-bold">Contact</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          For privacy requests, contact the Sanjivi AI team through the early access email channel provided to users.
        </p>
      </div>
    </main>
  );
}
