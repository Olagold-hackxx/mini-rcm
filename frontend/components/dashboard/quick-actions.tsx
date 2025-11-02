import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, FileText, Download } from "lucide-react"

export function QuickActions() {
  return (
    <Card className="border-border/50">
      <CardHeader>
        <CardTitle className="text-xl">Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button className="w-full justify-start gap-3" asChild>
          <Link href="/dashboard/upload">
            <Upload className="h-5 w-5" />
            Upload New Claims
          </Link>
        </Button>
        <Button variant="outline" className="w-full justify-start gap-3 bg-transparent" asChild>
          <Link href="/dashboard/results">
            <FileText className="h-5 w-5" />
            View Results
          </Link>
        </Button>
        <Button variant="outline" className="w-full justify-start gap-3 bg-transparent">
          <Download className="h-5 w-5" />
          Export Report
        </Button>
      </CardContent>
    </Card>
  )
}
