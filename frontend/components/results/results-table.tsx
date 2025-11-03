"use client"

import { useState, useEffect } from "react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { claimsApi } from "@/lib/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import ReactMarkdown from "react-markdown"

// Markdown component overrides for consistent styling
const markdownComponents: any = {
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="ml-4">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }: { children?: React.ReactNode }) => <em className="italic">{children}</em>,
  code: ({ children }: { children?: React.ReactNode }) => <code className="bg-background px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
}

interface Claim {
  claim_id: string
  status: string
  error_type: string
  service_date: string | null
  paid_amount_aed: number
  error_explanation?: string
  recommended_action?: string
  technical_errors?: any[]
  medical_errors?: any[]
  data_quality_errors?: any[]
  encounter_type?: string
  service_code?: string
  diagnosis_codes?: string[]
  llm_evaluated?: boolean
  llm_confidence_score?: number
  llm_explanation?: string
}

interface ResultsTableProps {
  readonly batchId?: string | null
}

export function ResultsTable({ batchId }: ResultsTableProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    async function fetchClaims() {
      try {
        setLoading(true)
        const response = await claimsApi.listClaims({
          limit: 100,
          batch_id: batchId || undefined,
          search: searchTerm || undefined,
        }) as { claims: Claim[] }
        setClaims(response.claims || [])
      } catch (err: any) {
        const errorMessage = err.message || "Failed to load claims"
        setError(errorMessage)
        toast.error(errorMessage)
      } finally {
        setLoading(false)
      }
    }

    const timeoutId = setTimeout(() => {
      fetchClaims()
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchTerm, batchId])

  const handleViewDetails = (claim: Claim) => {
    setSelectedClaim(claim)
    setDialogOpen(true)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "N/A"
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  const getMedicalValidationStatus = (claim: Claim): string => {
    const hasMedicalErrors = claim.medical_errors && claim.medical_errors.length > 0
    return hasMedicalErrors ? "FAIL" : "PASS"
  }

  const getTechnicalValidationStatus = (claim: Claim): string => {
    const hasTechnicalErrors = claim.technical_errors && claim.technical_errors.length > 0
    const hasDataQualityErrors = claim.data_quality_errors && claim.data_quality_errors.length > 0
    return (hasTechnicalErrors || hasDataQualityErrors) ? "FAIL" : "PASS"
  }

  const getOverallStatus = (claim: Claim): string => {
    if (claim.status === "Validated" && claim.error_type === "No error") {
      return "✅ VALID"
    }
    return "❌ INVALID"
  }

  const getFailureReasons = (claim: Claim): string => {
    const reasons: string[] = []
    
    // Add medical errors
    if (claim.medical_errors && claim.medical_errors.length > 0) {
      claim.medical_errors.forEach((error: any) => {
        if (error.detail) {
          reasons.push(error.detail)
        }
      })
    }
    
    // Add technical errors
    if (claim.technical_errors && claim.technical_errors.length > 0) {
      claim.technical_errors.forEach((error: any) => {
        if (error.detail) {
          reasons.push(error.detail)
        }
      })
    }
    
    // Add data quality errors
    if (claim.data_quality_errors && claim.data_quality_errors.length > 0) {
      claim.data_quality_errors.forEach((error: any) => {
        if (error.detail) {
          reasons.push(error.detail)
        }
      })
    }
    
    return reasons.join("; ") || "No errors"
  }

  if (loading && claims.length === 0) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-[200px] text-muted-foreground">
            Loading claims...
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error && claims.length === 0) {
    return (
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <div className="text-center text-destructive">{error}</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
    <Card className="border-border/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Claims Details</CardTitle>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search claims..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                  <TableHead className="font-semibold">Claim ID</TableHead>
                  <TableHead className="font-semibold">Medical Validation</TableHead>
                  <TableHead className="font-semibold">Technical Validation</TableHead>
                  <TableHead className="font-semibold">Overall Status</TableHead>
                  <TableHead className="font-semibold">Failure Reasons</TableHead>
                  <TableHead className="font-semibold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
                {claims.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      No claims found
                    </TableCell>
                  </TableRow>
                ) : (
                  claims.map((claim) => {
                    const medicalStatus = getMedicalValidationStatus(claim)
                    const technicalStatus = getTechnicalValidationStatus(claim)
                    const overallStatus = getOverallStatus(claim)
                    const failureReasons = getFailureReasons(claim)
                    
                    return (
                      <TableRow key={claim.claim_id}>
                        <TableCell className="font-medium">{claim.claim_id}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={medicalStatus === "PASS" ? "default" : "destructive"}
                            className={medicalStatus === "PASS" ? "bg-green-600" : ""}
                          >
                            {medicalStatus}
                          </Badge>
                        </TableCell>
                  <TableCell>
                          <Badge 
                            variant={technicalStatus === "PASS" ? "default" : "destructive"}
                            className={technicalStatus === "PASS" ? "bg-green-600" : ""}
                          >
                            {technicalStatus}
                          </Badge>
                  </TableCell>
                  <TableCell>
                          <span className={`font-medium ${
                            overallStatus.includes("✅") ? "text-green-600" : "text-red-600"
                          }`}>
                            {overallStatus}
                          </span>
                        </TableCell>
                        <TableCell className="max-w-md">
                          <div className="text-sm text-muted-foreground line-clamp-2">
                            {failureReasons}
                          </div>
                  </TableCell>
                  <TableCell>
                          <Button variant="ghost" size="sm" onClick={() => handleViewDetails(claim)}>
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
                    )
                  })
                )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Claim Details - {selectedClaim?.claim_id}</DialogTitle>
            <DialogDescription>Detailed information about the claim validation</DialogDescription>
          </DialogHeader>
          {selectedClaim && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Status</p>
                  <Badge variant={selectedClaim.status === "Validated" ? "default" : "destructive"}>
                    {selectedClaim.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Error Type</p>
                  <Badge variant={selectedClaim.error_type === "No error" ? "secondary" : "outline"}>
                    {selectedClaim.error_type}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Encounter Type</p>
                  <p className="text-sm">{selectedClaim.encounter_type || "N/A"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Service Code</p>
                  <p className="text-sm">{selectedClaim.service_code || "N/A"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Service Date</p>
                  <p className="text-sm">{formatDate(selectedClaim.service_date)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Paid Amount</p>
                  <p className="text-sm">{selectedClaim.paid_amount_aed.toLocaleString()} AED</p>
                </div>
              </div>

              {selectedClaim.diagnosis_codes && selectedClaim.diagnosis_codes.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Diagnosis Codes</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedClaim.diagnosis_codes.map((code, idx) => (
                      <Badge key={idx} variant="outline">
                        {code}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedClaim.error_explanation && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Error Explanation</p>
                  <div className="text-sm bg-muted p-3 rounded-md prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown components={markdownComponents}>
                      {selectedClaim.error_explanation}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {selectedClaim.recommended_action && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Recommended Action</p>
                  <div className="text-sm bg-muted p-3 rounded-md prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown components={markdownComponents}>
                      {selectedClaim.recommended_action}
                    </ReactMarkdown>
                  </div>
                </div>
              )}

              {selectedClaim.technical_errors && selectedClaim.technical_errors.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Technical Errors</p>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    {selectedClaim.technical_errors.map((error: any, idx: number) => (
                      <li key={idx}>{error.detail || JSON.stringify(error)}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedClaim.data_quality_errors && selectedClaim.data_quality_errors.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Data Quality Errors</p>
                  <ul className="text-sm space-y-1 list-disc list-inside">
                    {selectedClaim.data_quality_errors.map((error: any, idx: number) => (
                      <li key={idx}>{error.detail || JSON.stringify(error)}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedClaim.medical_errors && selectedClaim.medical_errors.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Medical Errors</p>
                  <div className="space-y-3">
                    {selectedClaim.medical_errors.map((error: any, idx: number) => (
                      <div key={idx} className="text-sm bg-muted p-3 rounded-md prose prose-sm max-w-none dark:prose-invert">
                        <ReactMarkdown components={markdownComponents}>
                          {error.detail || error.rule || JSON.stringify(error)}
                        </ReactMarkdown>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
