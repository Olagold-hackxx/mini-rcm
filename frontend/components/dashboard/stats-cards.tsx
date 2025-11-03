"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileCheck, AlertTriangle, CheckCircle, Clock } from "lucide-react"
import { analyticsApi } from "@/lib/api"
import { cn } from "@/lib/utils"

export function StatsCards() {
  const [metrics, setMetrics] = useState({
    total_claims: 0,
    validated_claims: 0,
    not_validated_claims: 0,
    validation_rate: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const data = await analyticsApi.getMetrics() as { summary: any }
        setMetrics(data.summary)
      } catch (err: any) {
        toast.error(err.message || "Failed to load statistics")
      } finally {
        setLoading(false)
      }
    }
    fetchMetrics()
  }, [])

  const stats = [
    {
      title: "Total Claims",
      value: loading ? "..." : metrics.total_claims.toLocaleString(),
      change: "",
      icon: FileCheck,
      color: "text-primary",
    },
    {
      title: "Validated",
      value: loading ? "..." : metrics.validated_claims.toLocaleString(),
      change: metrics.validation_rate > 0 ? `${metrics.validation_rate.toFixed(1)}%` : "",
      icon: CheckCircle,
      color: "text-accent",
    },
    {
      title: "Errors Found",
      value: loading ? "..." : metrics.not_validated_claims.toLocaleString(),
      change: "",
      icon: AlertTriangle,
      color: "text-destructive",
    },
    {
      title: "Validation Rate",
      value: loading ? "..." : `${metrics.validation_rate.toFixed(1)}%`,
      change: "",
      icon: Clock,
      color: "text-muted-foreground",
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title} className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
            <stat.icon className={cn("h-4 w-4", stat.color)} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-card-foreground">{stat.value}</div>
            {stat.change && <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
