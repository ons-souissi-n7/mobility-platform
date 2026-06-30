export default function StudentLandingPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F9FAFB]">
      <div className="max-w-md rounded-lg border bg-white p-8 shadow-sm text-center">
        <span className="text-2xl font-bold tracking-wider text-[#1E3A8A]">N7 MOBILITE</span>
        <p className="mt-4 text-sm text-gray-600">
          Accédez à votre espace personnel via le lien fourni par votre administration.
        </p>
        <p className="mt-2 text-xs text-gray-400">
          Format : /student/&lt;votre-INE&gt;/accords
        </p>
      </div>
    </div>
  );
}
