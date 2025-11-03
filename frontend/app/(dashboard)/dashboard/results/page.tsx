"use client"

import { useState } from "react"
import { ResultsCharts } from "@/components/results/results-charts"
import { ResultsTable } from "@/components/results/results-table"
import { WaterfallChart } from "@/components/results/waterfall-chart"
import { BatchSelector } from "@/components/results/batch-selector"

export default function ResultsPage() {
  const [selectedBatch, setSelectedBatch] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Validation Results</h1>
        <p className="text-muted-foreground">Detailed analysis of claims validation outcomes</p>
      </div>

      <BatchSelector selectedBatch={selectedBatch} onBatchChange={setSelectedBatch} />

      <ResultsCharts batchId={selectedBatch} />
      <WaterfallChart batchId={selectedBatch} />
      <ResultsTable batchId={selectedBatch} />
    </div>
  )
}
