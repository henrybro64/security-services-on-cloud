import "./globals.css";
import type { Metadata } from "next";



export const metadata: Metadata = {
  title: "Security Config Checker",
  description: "FastAPI + Redis cloud security scanner UI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body data-carbon-theme="g100">{children}</body>
    </html>
  );
}
