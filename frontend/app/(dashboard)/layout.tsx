import type React from "react"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardSidebar } from "@/components/dashboard/dashboard-sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      <div className="flex max-w-screen overflow-hidden">
        <DashboardSidebar />
        <main className="flex-1 p-6 lg:p-8 overflow-hidden">{children}</main>
      </div>
    </div>
  )
}
