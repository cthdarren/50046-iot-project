"use client";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { useId } from "@/context/IdContext";
import { useRouter } from "next/navigation";
import React, { useEffect } from "react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { id } = useId();

  // Redirect effect — safe
  useEffect(() => {
    if (id === null) {
      router.push("/admin");
    }
  }, [id, router]);

  if (id === null) return null;

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarTrigger />
      {children}
    </SidebarProvider>
  );
}
