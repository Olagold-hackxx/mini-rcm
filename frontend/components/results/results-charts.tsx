"use client"

import { useEffect, useState } from "react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { analyticsApi } from "@/lib/api"

interface ChartData {
  category: string
  count?: number
  amount?: number
}

interface ResultsChartsProps {
  batchId?: string | null
}

export function ResultsCharts({ batchId }: ResultsChartsProps) {
  const [errorBreakdown, setErrorBreakdown] = useState<ChartData[]>([])
  const [amountBreakdown, setAmountBreakdown] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const [errorData, amountData] = await Promise.all([
          analyticsApi.getErrorBreakdown(batchId || undefined),
          analyticsApi.getAmountBreakdown(batchId || undefined),
        ])
        setErrorBreakdown(errorData)
        setAmountBreakdown(amountData)
      } catch (err: any) {
        const errorMessage = err.message || "Failed to load chart data"
        setError(errorMessage)
        toast.error(errorMessage)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [batchId])

  if (loading) {
    return (
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Claims Count by Error Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              Loading...
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Paid Amount by Error Category (AED)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
              Loading...
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <div className="text-center text-destructive">{error}</div>
        </CardContent>
      </Card>
    )
  }

  // Use blue color scheme from app theme - using direct RGB values for better browser compatibility
  const getChartColor = (category: string) => {
    // Blue shades (hue 240 = blue)
    const blueShades: Record<string, string> = {
      // Main blue: oklch(0.52 0.14 240) ≈ rgb(59, 130, 246)
      primary: "#3b82f6", 
      // Accent blue: oklch(0.58 0.16 200) ≈ rgb(96, 165, 250)
      accent: "#60a5fa",
      // Lighter blue
      primaryLight: "#93c5fd",
      // Darker blue
      primaryDark: "#2563eb",
    }
    
    // Use blue shades based on category
    if (category === "No Error") return blueShades.accent
    if (category === "Technical Error") return blueShades.primaryDark
    if (category === "Medical Error") return blueShades.primary
    if (category === "Both Errors") return blueShades.primaryLight
    return blueShades.primary
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Claims Count by Error Category</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={errorBreakdown} barCategoryGap="8%">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis
                dataKey="category"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                height={80}
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickLine={{ stroke: "hsl(var(--border))" }}
              />
              <YAxis 
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} 
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickLine={{ stroke: "hsl(var(--border))" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                }}
                cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {errorBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getChartColor(entry.category)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Paid Amount by Error Category (AED)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={amountBreakdown} barCategoryGap="8%">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis
                dataKey="category"
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                height={80}
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickLine={{ stroke: "hsl(var(--border))" }}
              />
              <YAxis 
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} 
                axisLine={{ stroke: "hsl(var(--border))" }}
                tickLine={{ stroke: "hsl(var(--border))" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                }}
                formatter={(value: number) => `${value.toLocaleString("en-US", { maximumFractionDigits: 0 })} AED`}
                cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
              />
              <Bar dataKey="amount" radius={[6, 6, 0, 0]} maxBarSize={60}>
                {amountBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getChartColor(entry.category)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
