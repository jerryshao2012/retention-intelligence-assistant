import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Retention Intelligence Assistant",
  description: "Multi-agent retention intelligence for bankers"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
