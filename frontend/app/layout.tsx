import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "PickByMe",
  description: "Creator-led commerce and recommendations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <nav className="nav">
            <Link href="/" className="brand">Pick<span>ByMe</span></Link>
            <div className="actions">
              <Link href="/" className="btn">Discover</Link>
              <Link href="/login" className="btn">Login</Link>
              <Link href="/dashboard" className="btn primary">Dashboard</Link>
            </div>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
