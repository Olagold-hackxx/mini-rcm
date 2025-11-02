"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { FileUploadZone } from "@/components/upload/file-upload-zone"

export function UploadForm() {
  const router = useRouter()
  const [claimsFile, setClaimsFile] = useState<File | null>(null)
  const [technicalRules, setTechnicalRules] = useState<File | null>(null)
  const [medicalRules, setMedicalRules] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsProcessing(true)

    // Simulate processing
    setTimeout(() => {
      setIsProcessing(false)
      router.push("/dashboard/results")
    }, 2000)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Claims File</CardTitle>
        </CardHeader>
        <CardContent>
          <FileUploadZone
            label="Upload claims data file (CSV, Excel)"
            file={claimsFile}
            onFileChange={setClaimsFile}
            accept=".csv,.xlsx,.xls"
          />
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Adjudication Rules</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="mb-2 block">Technical Rules Document</Label>
            <FileUploadZone
              label="Upload technical adjudication rules"
              file={technicalRules}
              onFileChange={setTechnicalRules}
              accept=".pdf,.docx,.txt"
            />
          </div>
          <div>
            <Label className="mb-2 block">Medical Rules Document</Label>
            <FileUploadZone
              label="Upload medical adjudication rules"
              file={medicalRules}
              onFileChange={setMedicalRules}
              accept=".pdf,.docx,.txt"
            />
          </div>
        </CardContent>
      </Card>

      <Button
        type="submit"
        size="lg"
        className="w-full"
        disabled={!claimsFile || !technicalRules || !medicalRules || isProcessing}
      >
        {isProcessing ? "Processing Claims..." : "Start Validation"}
      </Button>
    </form>
  )
}
