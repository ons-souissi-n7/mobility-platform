"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

function LoginContent() {
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";
  const error = searchParams.get("error");

  useEffect(() => {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
    const timer = setTimeout(() => {
      window.location.href = `${apiUrl}/auth/login/?next=${encodeURIComponent(next)}`;
    }, 600);
    return () => clearTimeout(timer);
  }, [next]);

  const errorMessages: Record<string, string> = {
    cas_unavailable: "Le service CAS est indisponible. Réessayez.",
    invalid_ticket: "Ticket CAS invalide. Veuillez vous reconnecter.",
    auth_failed: "Erreur d'authentification. Veuillez réessayer.",
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-md text-center">
        <div className="mb-4 text-2xl font-bold text-[#1a2b4a]">
          N7 Mobilité
        </div>
        {error && (
          <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessages[error] ?? "Erreur d'authentification."}
          </div>
        )}
        <p className="text-sm text-gray-500">
          Redirection vers le portail CAS…
        </p>
        <div className="mt-4 flex justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#1a2b4a] border-t-transparent" />
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#1a2b4a] border-t-transparent" />
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
