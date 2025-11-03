"use client"

import { useState, useEffect } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { analyticsApi } from "@/lib/api"
import { Loader2 } from "lucide-react"

interface Batch {
  batch_id: string
  claim_count: number
  validated_count: number
  total_amount: number
  created_at: string | null
  processed_at: string | null
}

interface BatchSelectorProps {
  readonly selectedBatch: string | null
  readonly onBatchChange: (batchId: string | null) => void
}

export function BatchSelector({ selectedBatch, onBatchChange }: BatchSelectorProps) {
  const [batches, setBatches] = useState<Batch[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchBatches() {
      try {
        setLoading(true)
        const response = await analyticsApi.getBatches() as { batches: Batch[] }
        setBatches(response.batches || [])
      } catch (error) {
        console.error("Failed to fetch batches:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchBatches()
  }, [])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A"
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    } catch {
      return "N/A"
    }
  }

  const selectedBatchData = batches.find(b => b.batch_id === selectedBatch)

  if (loading) {
    return (
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Batch Selection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border/50">
      <CardHeader>
        <CardTitle>Batch Selection</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-foreground mb-2 block">
            Select Batch
          </label>
          <Select
            value={selectedBatch || "all"}
            onValueChange={(value) => onBatchChange(value === "all" ? null : value)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All Batches" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Batches</SelectItem>
              {batches.map((batch) => (
                <SelectItem key={batch.batch_id} value={batch.batch_id}>
                  {batch.batch_id} ({batch.claim_count} claims)
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedBatchData && (
          <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Total Claims:</span>
              <span className="font-medium">{selectedBatchData.claim_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Validated:</span>
              <span className="font-medium">{selectedBatchData.validated_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Total Amount:</span>
              <span className="font-medium">{selectedBatchData.total_amount.toLocaleString("en-US", { maximumFractionDigits: 2 })} AED</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Uploaded:</span>
              <span className="font-medium">{formatDate(selectedBatchData.created_at)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Processed:</span>
              <span className="font-medium">{formatDate(selectedBatchData.processed_at)}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

