"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

const mockData = [
  {
    claimId: "CLM-2024-001",
    encounterType: "Outpatient",
    serviceDate: "2024-01-15",
    nationalId: "784-1234-5678",
    memberId: "MEM-001",
    facilityId: "FAC-101",
    diagnosisCodes: "J18.9, R50.9",
    serviceCode: "99213",
    paidAmount: 2450,
    status: "Validated",
    errorType: "No error",
    explanation: "All validation checks passed successfully.",
    recommendation: "Proceed with payment processing.",
  },
  {
    claimId: "CLM-2024-002",
    encounterType: "Inpatient",
    serviceDate: "2024-01-16",
    nationalId: "784-2345-6789",
    memberId: "MEM-002",
    facilityId: "FAC-102",
    diagnosisCodes: "I10, E11.9",
    serviceCode: "99223",
    paidAmount: 5800,
    status: "Not validated",
    errorType: "Technical error",
    explanation:
      "• Service code does not match encounter type\n• Missing required approval number for inpatient service",
    recommendation: "Verify service code and obtain approval number before resubmission.",
  },
]

export function ResultsTable() {
  const [searchTerm, setSearchTerm] = useState("")

  const filteredData = mockData.filter(
    (item) =>
      item.claimId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.memberId.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
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
                <TableHead>Claim ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Error Type</TableHead>
                <TableHead>Service Date</TableHead>
                <TableHead>Paid Amount</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((claim) => (
                <TableRow key={claim.claimId}>
                  <TableCell className="font-medium">{claim.claimId}</TableCell>
                  <TableCell>
                    <Badge variant={claim.status === "Validated" ? "default" : "destructive"}>{claim.status}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={claim.errorType === "No error" ? "secondary" : "outline"}>{claim.errorType}</Badge>
                  </TableCell>
                  <TableCell>{claim.serviceDate}</TableCell>
                  <TableCell>{claim.paidAmount.toLocaleString()} AED</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm">
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
