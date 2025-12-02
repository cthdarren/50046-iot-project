"use client";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbSeparator } from "@/components/ui/breadcrumb";

import { useId } from "@/context/IdContext";
import { useRouter, usePathname } from "next/navigation";
import React, { useEffect } from "react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { id, loaded } = useId();

  // Redirect if no mall ID (your auth logic)
  useEffect(() => {
    if (loaded && id === null) {
      router.push("/admin");
    }
  }, [loaded, id, router]);

  if (id === null) return null;

  // ------------------------------------------
  // Generate breadcrumbs from pathname
  // ------------------------------------------
const segments = pathname.split("/").filter(Boolean).slice(2); // skip 'admin/dashboard'

let breadcrumbItems: { href: string; label: string }[] = [];

for (let i = 0; i < segments.length; i++) {
  const seg = segments[i];
  const prev = segments[i - 1];

  // 1️⃣ If the segment is numeric → combine with previous label
  if (/^\d+$/.test(seg) && prev) {
    breadcrumbItems[breadcrumbItems.length - 1] = {
      href: pathname, // full path
      label:
        prev.replace(/-/g, " ").replace(/^\w/, (c) => c.toUpperCase()) +
        " " +
        seg,
    };
    continue;
  }

  // 2️⃣ Normal segment behavior
  const href = "/admin/" + segments.slice(0, i + 1).join("/");

  const label = seg
    .replace(/-/g, " ")
    .replace(/^\w/, (c) => c.toUpperCase());

  breadcrumbItems.push({ href, label });
}
  return (
    <SidebarProvider>
      <AppSidebar />

      <div className="flex flex-col flex-1 p-6">
        <SidebarTrigger />
        <Breadcrumb className="my-4">
          <BreadcrumbList>

            <BreadcrumbItem>
              <BreadcrumbLink href="/admin/dashboard">Dashboard</BreadcrumbLink>
            </BreadcrumbItem>

            {breadcrumbItems.length > 0 && <BreadcrumbSeparator />}

            {breadcrumbItems.map((item, i) => (
              <React.Fragment key={item.href}>
                <BreadcrumbItem>
                  <BreadcrumbLink href={item.href}>
                    {item.label}
                  </BreadcrumbLink>
                </BreadcrumbItem>

                {i < breadcrumbItems.length - 1 && <BreadcrumbSeparator />}
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>

        {/* Children */}
        {children}
      </div>
    </SidebarProvider>
  );
}
