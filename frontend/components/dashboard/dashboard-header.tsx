"use client"

import Link from "next/link"
import { Activity, Bell, User, Building2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useEffect, useState } from "react"
import { authApi } from "@/lib/api"

interface UserInfo {
  username: string
  tenant_id?: string
  email?: string
}

export function DashboardHeader() {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchUserInfo() {
      try {
        const user = await authApi.getMe()
        setUserInfo(user)
      } catch (error) {
        // User not logged in or error fetching
        console.error("Failed to fetch user info:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchUserInfo()
  }, [])

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex h-16 items-center gap-4 px-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Activity className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold text-foreground">MediClaim AI</span>
        </Link>

        <div className="ml-auto flex items-center gap-3">
          {!loading && userInfo && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/50 border border-border/50">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">Tenant:</span>
              <Badge variant="secondary" className="text-xs font-mono">
                {userInfo.tenant_id || "default"}
              </Badge>
            </div>
          )}
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <User className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  )
}
