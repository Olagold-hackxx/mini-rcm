"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileUploadZone } from "@/components/upload/file-upload-zone"
import { FilePreview } from "@/components/upload/file-preview"

export function UploadForm() {
  const router = useRouter()
  const [claimsFile, setClaimsFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!claimsFile) {
      toast.error("Please upload a claims file")
      return
    }

    setIsProcessing(true)

    try {
      const { uploadApi } = await import("@/lib/api")
      await uploadApi.uploadClaimsFile(claimsFile)
      
      toast.success("Claims file uploaded successfully")
      
      // Redirect to results page
      router.push("/dashboard/results")
    } catch (error: any) {
      toast.error(error.message || "Failed to upload file. Please try again.")
      setIsProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-6">
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

      {claimsFile && (
        <div className="w-full overflow-hidden">
          <FilePreview file={claimsFile} maxRows={10} />
        </div>
      )}

      <div className="rounded-lg border border-border/50 bg-muted/30 p-4">
        <p className="text-sm text-muted-foreground">
          <strong>Note:</strong> Adjudication rules are automatically loaded from the system. 
          Technical and medical rules are managed separately via the backend configuration.
        </p>
      </div>

      <Button
        type="submit"
        size="lg"
        className="w-full"
        disabled={!claimsFile || isProcessing}
      >
        {isProcessing ? "Processing Claims..." : "Start Validation"}
      </Button>
    </form>
  )
}
