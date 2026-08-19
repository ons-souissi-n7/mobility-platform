"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { getDefaultPath, parseToken, setToken } from "@/lib/auth";

function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const token = searchParams.get("token");
    const next = searchParams.get("next") ?? "/";

    if (!token) {
      router.replace("/login?error=auth_failed");
      return;
    }

    setToken(token);

    const payload = parseToken(token);
    if (!payload) {
      router.replace("/login?error=auth_failed");
      return;
    }

    // If next is /, go to the role-specific default; otherwise honour the original destination
    const destination = next === "/" ? getDefaultPath(payload) : next;
    router.replace(destination);
  }, [searchParams, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm rounded-xl bg-white p-8 shadow-md text-center">
        <div className="mb-4 text-2xl font-bold text-[#1a2b4a]">
          N7 Mobilité
        </div>
        <p className="text-sm text-gray-500">Connexion en cours…</p>
        <div className="mt-4 flex justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#1a2b4a] border-t-transparent" />
        </div>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#1a2b4a] border-t-transparent" />
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
