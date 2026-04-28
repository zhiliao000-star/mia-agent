import type { Metadata } from "next";
import "./styles.css";
import { ConvexClientProvider } from "../components/convex-client-provider";

export const metadata: Metadata = {
  title: "Mia Debug Dashboard",
  description: "Realtime operations dashboard for Mia personal AI agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ConvexClientProvider>{children}</ConvexClientProvider>
      </body>
    </html>
  );
}
