import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "N7 Mobilite",
  description: "Plateforme de gestion des mobilites internationales",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
