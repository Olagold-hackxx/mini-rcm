"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const claimCountData = [
  { category: "No Error", count: 1156, fill: "hsl(var(--chart-2))" },
  { category: "Technical Error", count: 78, fill: "hsl(var(--chart-1))" },
  { category: "Medical Error", count: 42, fill: "hsl(var(--chart-5))" },
  { category: "Both Errors", count: 8, fill: "hsl(var(--chart-3))" },
]

const paidAmountData = [
  { category: "No Error", amount: 2845600, fill: "hsl(var(--chart-2))" },
  { category: "Technical Error", amount: 156800, fill: "hsl(var(--chart-1))" },
  { category: "Medical Error", amount: 89400, fill: "hsl(var(--chart-5))" },
  { category: "Both Errors", amount: 18200, fill: "hsl(var(--chart-3))" },
]

export function ResultsCharts() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Claims Count by Error Category</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={claimCountData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="category" tick={{ fill: "hsl(var(--muted-foreground))" }} fontSize={12} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
              />
              <Bar dataKey="count" radius={[8, 8, 0, 0]} />
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
            <BarChart data={paidAmountData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="category" tick={{ fill: "hsl(var(--muted-foreground))" }} fontSize={12} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))" }} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
                formatter={(value: number) => `${value.toLocaleString()} AED`}
              />
              <Bar dataKey="amount" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
