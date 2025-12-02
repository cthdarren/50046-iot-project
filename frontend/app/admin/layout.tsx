import "../globals.css";
import { IdProvider } from "@/context/IdContext";

export default function Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <IdProvider>
        {children}
    </IdProvider>
  );
}
