"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { rulesApi, tenantsApi } from "@/lib/api"
import { toast } from "sonner"

interface RulesData {
  technical?: any
  medical?: any
}

export default function RulesManagement() {
  const [ruleType, setRuleType] = useState<"technical" | "medical">("technical")
  const [rules, setRules] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [validationStatus, setValidationStatus] = useState<any>(null)
  const [currentTenantInfo, setCurrentTenantInfo] = useState<any>(null)
  const isDefaultTenant = currentTenantInfo?.tenant_id === "default"

  useEffect(() => {
    loadCurrentTenant()
  }, [])

  useEffect(() => {
    loadRules()
    validateRules()
  }, [ruleType])

  const loadCurrentTenant = async () => {
    try {
      const info = await tenantsApi.getCurrentTenant()
      setCurrentTenantInfo(info)
    } catch (error) {
      console.error("Failed to load tenant info:", error)
    }
  }

  const loadRules = async () => {
    setLoading(true)
    try {
      const data = await rulesApi.getRules(ruleType) as RulesData
      setRules(data[ruleType] || {})
    } catch (error: any) {
      toast.error(`Failed to load rules: ${error.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  const validateRules = async () => {
    try {
      const status = await rulesApi.validateRules(ruleType)
      setValidationStatus(status)
    } catch (error: any) {
      console.error("Failed to validate rules:", error)
    }
  }

  const handleSave = async () => {
    if (!rules) return

    setSaving(true)
    try {
      await rulesApi.updateRules(ruleType, rules)
      toast.success(`${ruleType} rules updated successfully`)
      await validateRules()
    } catch (error: any) {
      toast.error(`Failed to update rules: ${error.message || "Unknown error"}`)
    } finally {
      setSaving(false)
    }
  }

  const handleReload = async () => {
    setLoading(true)
    try {
      await rulesApi.reloadRules(ruleType)
      toast.success("Rules cache invalidated")
      await loadRules()
      await validateRules()
    } catch (error: any) {
      toast.error(`Failed to reload rules: ${error.message || "Unknown error"}`)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith(".json")) {
      toast.error("Please upload a JSON file")
      return
    }

    setUploading(true)
    try {
      await rulesApi.uploadRulesFile(ruleType, file)
      toast.success(`Rules file uploaded successfully`)
      await loadRules()
      await validateRules()
    } catch (error: any) {
      toast.error(`Failed to upload file: ${error.message || "Unknown error"}`)
    } finally {
      setUploading(false)
      // Reset input
      event.target.value = ""
    }
  }

  const updateRuleField = (path: string[], value: any) => {
    if (!rules) return

    const newRules = structuredClone(rules)
    let current: any = newRules

    for (let i = 0; i < path.length - 1; i++) {
      if (!(path[i] in current)) {
        current[path[i]] = {}
      }
      current = current[path[i]]
    }

    current[path[path.length - 1]] = value
    setRules(newRules)
  }

  if (loading && !rules) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">Loading rules...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rule Configuration</CardTitle>
          <CardDescription>
            Manage technical and medical validation rules for your tenant
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isDefaultTenant && (
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>⚠️ Default Tenant:</strong> Rules cannot be modified for the default tenant.
                Please create a new tenant to customize rules.
              </p>
            </div>
          )}

          <div className="flex items-center gap-4">
            <div className="space-y-2 flex-1">
              <Label>Rule Type</Label>
              <Select value={ruleType} onValueChange={(value) => setRuleType(value as "technical" | "medical")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="technical">Technical Rules</SelectItem>
                  <SelectItem value="medical">Medical Rules</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {validationStatus && (
              <div className="space-y-2">
                <Label>Status</Label>
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${validationStatus.exists ? "text-green-600" : "text-yellow-600"}`}>
                    {validationStatus.exists ? "✓ Custom" : "⚠ Default"}
                  </span>
                  {validationStatus.file_path && (
                    <span className="text-xs text-muted-foreground">
                      {validationStatus.file_path.split("/").pop()}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {ruleType === "technical" && rules && (
            <div className="space-y-4 border rounded-lg p-4">
              <div className="space-y-2">
                <Label>Paid Amount Threshold (AED)</Label>
                <Input
                  type="number"
                  value={rules.paid_amount_threshold || 5000}
                  onChange={(e) => updateRuleField(["paid_amount_threshold"], Number.parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="space-y-2">
                <Label>Services Requiring Approval (comma-separated)</Label>
                <Input
                  value={Array.isArray(rules.services_requiring_approval) ? rules.services_requiring_approval.join(", ") : ""}
                  onChange={(e) => {
                    const services = e.target.value.split(",").map(s => s.trim()).filter(Boolean)
                    updateRuleField(["services_requiring_approval"], services)
                  }}
                  placeholder="SRV1001, SRV1002, SRV2008"
                />
              </div>

              <div className="space-y-2">
                <Label>Diagnoses Requiring Approval (comma-separated)</Label>
                <Input
                  value={Array.isArray(rules.diagnoses_requiring_approval) ? rules.diagnoses_requiring_approval.join(", ") : ""}
                  onChange={(e) => {
                    const diagnoses = e.target.value.split(",").map(d => d.trim()).filter(d => d)
                    updateRuleField(["diagnoses_requiring_approval"], diagnoses)
                  }}
                  placeholder="E11.9, R07.9, Z34.0"
                />
              </div>

              <div className="space-y-2">
                <Label>Unique ID Pattern (regex)</Label>
                <Input
                  value={rules.unique_id_pattern || ""}
                  onChange={(e) => updateRuleField(["unique_id_pattern"], e.target.value)}
                  placeholder="^[A-Z0-9-]{10,}$"
                />
              </div>
            </div>
          )}

          {ruleType === "medical" && rules && (
            <div className="space-y-4 border rounded-lg p-4">
              <div className="space-y-2">
                <Label>Inpatient Services (comma-separated)</Label>
                <Input
                  value={Array.isArray(rules.inpatient_services) ? rules.inpatient_services.join(", ") : ""}
                  onChange={(e) => {
                    const services = e.target.value.split(",").map(s => s.trim()).filter(s => s)
                    updateRuleField(["inpatient_services"], services)
                  }}
                  placeholder="SRV1001, SRV1002, SRV1003"
                />
              </div>

              <div className="space-y-2">
                <Label>Outpatient Services (comma-separated)</Label>
                <Input
                  value={Array.isArray(rules.outpatient_services) ? rules.outpatient_services.join(", ") : ""}
                  onChange={(e) => {
                    const services = e.target.value.split(",").map(s => s.trim()).filter(s => s)
                    updateRuleField(["outpatient_services"], services)
                  }}
                  placeholder="SRV2001, SRV2002, SRV2007"
                />
              </div>

              <div className="text-sm text-muted-foreground">
                <p>Note: Complex medical rules (service-diagnosis requirements, facility mappings, etc.) should be managed via JSON file upload.</p>
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-4">
            <Button onClick={handleSave} disabled={saving || !rules || isDefaultTenant}>
              {saving ? "Saving..." : "Save Changes"}
            </Button>
            <Button variant="outline" onClick={handleReload} disabled={loading}>
              Reload from File
            </Button>
            <div className="relative">
              <Button variant="outline" disabled={uploading || isDefaultTenant} asChild>
                <label htmlFor={`file-upload-${ruleType}`} className="cursor-pointer">
                  {uploading ? "Uploading..." : "Upload JSON File"}
                </label>
              </Button>
              <Input
                id={`file-upload-${ruleType}`}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFileUpload}
                disabled={isDefaultTenant}
              />
            </div>
          </div>

          <div className="text-xs text-muted-foreground pt-2 border-t">
            <p>• Rules are automatically cached and reloaded when files change</p>
            <p>• Upload a complete JSON file to replace all rules at once</p>
            <p>• Changes take effect immediately for new claims</p>
          </div>
        </CardContent>
      </Card>

      {rules && (
        <Card>
          <CardHeader>
            <CardTitle>Raw JSON View</CardTitle>
            <CardDescription>View and edit the complete rules JSON</CardDescription>
          </CardHeader>
          <CardContent>
            <textarea
              className="w-full h-64 p-3 font-mono text-sm border rounded-md bg-background"
              value={JSON.stringify(rules, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value)
                  setRules(parsed)
                } catch {
                  // Invalid JSON, don't update
                }
              }}
            />
            <Button onClick={handleSave} className="mt-4" disabled={saving}>
              Save JSON Changes
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

