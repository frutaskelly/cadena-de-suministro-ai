import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { TenantProvider } from "@/components/TenantProvider";
import DevRoutePill from "@/components/DevRoutePill";

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
        <TenantProvider>
          <Sidebar />
          <div className="ml-60 min-h-screen">{children}</div>
          <DevRoutePill />
        </TenantProvider>
      </body>
    </html>
  );
}
