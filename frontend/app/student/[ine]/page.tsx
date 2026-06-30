import { redirect } from "next/navigation";

export default async function StudentInePage({ params }: { params: Promise<{ ine: string }> }) {
  const { ine } = await params;
  redirect(`/student/${ine}/accords`);
}
