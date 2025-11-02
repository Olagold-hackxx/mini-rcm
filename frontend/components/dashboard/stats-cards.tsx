import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileCheck, AlertTriangle, CheckCircle, Clock } from "lucide-react"

const stats = [
  {
    title: "Total Claims",
    value: "1,284",
    change: "+12.5%",
    icon: FileCheck,
    color: "text-primary",
  },
  {
    title: "Validated",
    value: "1,156",
    change: "+8.2%",
    icon: CheckCircle,
    color: "text-accent",
  },
  {
    title: "Errors Found",
    value: "128",
    change: "-4.3%",
    icon: AlertTriangle,
    color: "text-destructive",
  },
  {
    title: "Processing",
    value: "24",
    change: "Real-time",
    icon: Clock,
    color: "text-muted-foreground",
  },
]

export function StatsCards() {
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
            <p className="text-xs text-muted-foreground mt-1">{stat.change} from last month</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(" ")
}
