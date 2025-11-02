import { ResultsCharts } from "@/components/results/results-charts"
import { ResultsTable } from "@/components/results/results-table"

export default function ResultsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Validation Results</h1>
        <p className="text-muted-foreground">Detailed analysis of claims validation outcomes</p>
      </div>

      <ResultsCharts />
      <ResultsTable />
    </div>
  )
}
