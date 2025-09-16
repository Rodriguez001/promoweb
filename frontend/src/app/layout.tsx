import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "PromoWeb Africa - Produits Européens de Qualité",
  description: "Plateforme e-commerce spécialisée dans les produits européens de parapharmacie, beauté, bien-être et livres pour le Cameroun",
  keywords: "parapharmacie, beauté, bien-être, livres, produits européens, Cameroun, Douala, Yaoundé",
  authors: [{ name: "PromoWeb Africa Team" }],
  openGraph: {
    title: "PromoWeb Africa - Produits Européens de Qualité",
    description: "Découvrez notre sélection de produits européens de parapharmacie, beauté, bien-être et livres",
    type: "website",
    locale: "fr_FR",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="scroll-smooth">
      <body className={`${inter.variable} font-sans antialiased bg-white text-gray-900`}>
        <Navbar />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
