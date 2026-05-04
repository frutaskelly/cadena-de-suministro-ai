import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Cadena de Suministro AI",
  description: "ERP operativo para distribuidores B2B/B2G",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full">
        <Sidebar />
        <div className="ml-60 min-h-screen">{children}</div>
      </body>
    </html>
  );
}
