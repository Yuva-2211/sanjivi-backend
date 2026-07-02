import Link from "next/link";

export default function AyushDisclaimersPage() {
  return (
    <main className="min-h-screen bg-brand-bg px-6 py-16 text-brand-text">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="text-xs font-bold text-primary hover:underline">Back to Sanjivi AI</Link>
        <h1 className="mt-8 text-4xl font-black font-serif">AYUSH Disclaimers</h1>
        <p className="mt-4 text-sm text-brand-muted leading-relaxed">
          Sanjivi AI references Ayurveda, Yoga, Siddha, Unani, and Homeopathy for educational purposes. It is not a substitute for licensed medical advice, clinical diagnosis, or emergency care.
        </p>
        <h2 className="mt-8 text-lg font-bold">Emergency symptoms</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          For chest pain, stroke symptoms, severe breathing difficulty, loss of consciousness, poisoning, severe allergic reactions, suicidal thoughts, or major injury, call local emergency services immediately.
        </p>
        <h2 className="mt-8 text-lg font-bold">Contraindications</h2>
        <p className="mt-2 text-sm text-brand-muted leading-relaxed">
          Herbs, remedies, breathing practices, and yoga postures can be unsafe for some people. Always check with a qualified practitioner before using any recommendation.
        </p>
      </div>
    </main>
  );
}
