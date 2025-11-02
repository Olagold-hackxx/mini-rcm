import { UploadForm } from "@/components/upload/upload-form"

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Upload Claims</h1>
        <p className="text-muted-foreground">Upload claims files and adjudication rules for validation</p>
      </div>

      <UploadForm />
    </div>
  )
}
