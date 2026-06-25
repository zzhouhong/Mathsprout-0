"use client";

import { DashboardTabs } from "@/components/dashboard-tabs";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      className="flex flex-col min-h-screen"
      style={{ backgroundColor: "var(--kid-cream)" }}
    >
      <DashboardTabs />
      <main
        className="flex-1 flex flex-col min-w-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 20% 80%, var(--kid-bg-bubblegum) 0%, transparent 50%), radial-gradient(circle at 80% 20%, var(--kid-bg-sky) 0%, transparent 50%)",
        }}
      >
        {children}
      </main>
    </div>
  );
}
