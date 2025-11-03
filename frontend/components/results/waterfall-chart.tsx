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

interface WaterfallData {
  category: string
  value: number
  type: string
}

interface WaterfallChartProps {
  readonly batchId?: string | null
}

export function WaterfallChart({ batchId }: WaterfallChartProps) {
  const [waterfallData, setWaterfallData] = useState<WaterfallData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const metrics = await analyticsApi.getMetrics(batchId || undefined) as any
        
        // Process waterfall data
        let runningTotal = 0
        const processedData: WaterfallData[] = []
        
        for (const item of metrics.waterfall || []) {
          if (item.type === "start") {
            runningTotal = item.value
            processedData.push({ ...item, value: runningTotal })
          } else if (item.type === "end") {
            processedData.push({ ...item, value: runningTotal })
          } else {
            runningTotal += item.value
            processedData.push({ ...item, value: runningTotal })
          }
        }
        
        setWaterfallData(processedData)
      } catch (err: any) {
        const errorMessage = err.message || "Failed to load waterfall chart data"
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
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Claims Validation Waterfall</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[400px] text-muted-foreground">
            Loading...
          </div>
        </CardContent>
      </Card>
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

  // Use blue color scheme from app theme - using direct RGB values
  const getColor = (type: string, value: number) => {
    const blueShades: Record<string, string> = {
      primary: "#3b82f6",      // Main blue
      accent: "#60a5fa",        // Accent blue
      primaryLight: "#93c5fd",  // Lighter blue
      primaryDark: "#2563eb",   // Darker blue
    }
    
    if (type === "start" || type === "end") return blueShades.accent
    if (value > 0) return blueShades.primary
    return blueShades.primaryDark
  }

  return (
    <Card className="border-border/50">
      <CardHeader>
        <CardTitle>Claims Validation Waterfall</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={waterfallData} barCategoryGap="8%">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            <XAxis
              dataKey="category"
              tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={100}
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
              formatter={(value: number) => value.toLocaleString()}
              cursor={{ fill: "rgba(59, 130, 246, 0.1)" }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
              {waterfallData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(entry.type, entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

