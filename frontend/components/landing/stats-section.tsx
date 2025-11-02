import { Card, CardContent } from "@/components/ui/card"

const stats = [
  { value: "99.8%", label: "Validation Accuracy" },
  { value: "80%", label: "Time Reduction" },
  { value: "50K+", label: "Claims Processed Daily" },
  { value: "24/7", label: "Automated Processing" },
]

export function StatsSection() {
  return (
    <section className="py-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Card key={stat.label} className="border-border/50 bg-card text-center">
              <CardContent className="p-6">
                <div className="mb-2 text-4xl font-bold text-primary">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
