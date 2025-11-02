"use client"

import type React from "react"

import { useRef } from "react"
import { Upload, X, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"

interface FileUploadZoneProps {
  label: string
  file: File | null
  onFileChange: (file: File | null) => void
  accept?: string
}

export function FileUploadZone({ label, file, onFileChange, accept }: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleClick = () => {
    inputRef.current?.click()
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      onFileChange(selectedFile)
    }
  }

  const handleRemove = () => {
    onFileChange(null)
    if (inputRef.current) {
      inputRef.current.value = ""
    }
  }

  return (
    <div>
      <input ref={inputRef} type="file" className="hidden" accept={accept} onChange={handleChange} />

      {!file ? (
        <button
          type="button"
          onClick={handleClick}
          className="w-full rounded-lg border-2 border-dashed border-border bg-muted/30 p-8 text-center transition-colors hover:border-primary hover:bg-muted/50"
        >
          <Upload className="mx-auto mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground mb-1">{label}</p>
          <p className="text-xs text-muted-foreground">Click to browse or drag and drop</p>
        </button>
      ) : (
        <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-card-foreground">{file.name}</p>
              <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(2)} KB</p>
            </div>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={handleRemove}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
