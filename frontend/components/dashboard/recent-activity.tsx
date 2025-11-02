import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const activities = [
  {
    id: 1,
    claim: "CLM-2024-001",
    status: "validated",
    time: "2 minutes ago",
  },
  {
    id: 2,
    claim: "CLM-2024-002",
    status: "error",
    time: "5 minutes ago",
  },
  {
    id: 3,
    claim: "CLM-2024-003",
    status: "validated",
    time: "12 minutes ago",
  },
  {
    id: 4,
    claim: "CLM-2024-004",
    status: "processing",
    time: "15 minutes ago",
  },
]

export function RecentActivity() {
  return (
    <Card className="border-border/50">
      <CardHeader>
        <CardTitle className="text-xl">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-center justify-between">
              <div>
                <p className="font-medium text-card-foreground">{activity.claim}</p>
                <p className="text-sm text-muted-foreground">{activity.time}</p>
              </div>
              <Badge
                variant={
                  activity.status === "validated"
                    ? "default"
                    : activity.status === "error"
                      ? "destructive"
                      : "secondary"
                }
              >
                {activity.status}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
