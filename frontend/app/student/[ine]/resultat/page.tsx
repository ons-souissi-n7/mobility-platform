import { redirect } from "next/navigation";

export default async function ResultatRedirectPage({ params }: { params: Promise<{ ine: string }> }) {
  const { ine } = await params;
  redirect(`/student/${ine}/mobilite`);
}
