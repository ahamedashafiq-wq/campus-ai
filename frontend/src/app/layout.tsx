import type { Metadata } from "next";
import { Source_Sans_3 } from "next/font/google";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const sans = Source_Sans_3({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "CampusMatch AI",
  description: "Campus placement, resume intelligence, and explainable job matching.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${sans.className} antialiased`}>
        <AuthProvider>
          {children}
          <Toaster richColors position="top-right" />
        </AuthProvider>
      </body>
    </html>
  );
}
