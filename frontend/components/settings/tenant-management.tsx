"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { tenantsApi } from "@/lib/api"
import { toast } from "sonner"

interface TenantInfo {
  tenant_id: string
  exists: boolean
  has_custom_rules: boolean
  technical_rules_path?: string
  medical_rules_path?: string
}

interface TenantListItem {
  tenant_id: string
  has_rules: boolean
  is_default: boolean
  is_current: boolean
}

export default function TenantManagement() {
  const [currentTenant, setCurrentTenant] = useState<TenantInfo | null>(null)
  const [tenants, setTenants] = useState<TenantListItem[]>([])
  const [newTenantId, setNewTenantId] = useState("")
  const [creating, setCreating] = useState(false)
  const [switching, setSwitching] = useState(false)
  const [copyFromDefault, setCopyFromDefault] = useState(true)

  useEffect(() => {
    loadTenantInfo()
    loadTenantsList()
  }, [])

  const loadTenantInfo = async () => {
    try {
      const info = await tenantsApi.getCurrentTenant() as TenantInfo
      setCurrentTenant(info)
    } catch (error: any) {
      toast.error(`Failed to load tenant info: ${error.message || "Unknown error"}`)
    }
  }

  const loadTenantsList = async () => {
    try {
      const data = await tenantsApi.listTenants() as { tenants: TenantListItem[] }
      setTenants(data.tenants)
    } catch (error: any) {
      console.error("Failed to load tenants list:", error)
    }
  }

  const handleCreateTenant = async () => {
    if (!newTenantId.trim()) {
      toast.error("Please enter a tenant ID")
      return
    }

    if (newTenantId.toLowerCase() === "default") {
      toast.error("Cannot create a tenant with ID 'default'. This is reserved.")
      return
    }

    // Validate format (alphanumeric, underscore, hyphen)
    if (!/^[a-zA-Z0-9_-]+$/.test(newTenantId)) {
      toast.error("Tenant ID can only contain letters, numbers, underscores, and hyphens")
      return
    }

    setCreating(true)
    try {
      await tenantsApi.createTenant(newTenantId, copyFromDefault)
      toast.success(`Tenant '${newTenantId}' created successfully!`)
      setNewTenantId("")
      await loadTenantInfo()
      await loadTenantsList()
      // Refresh page to update tenant context
      globalThis.window.location.reload()
    } catch (error: any) {
      toast.error(`Failed to create tenant: ${error.message || "Unknown error"}`)
    } finally {
      setCreating(false)
    }
  }

  const handleSwitchTenant = async (tenantId: string) => {
    if (tenantId === currentTenant?.tenant_id) {
      toast.info("You are already using this tenant")
      return
    }

    setSwitching(true)
    try {
      await tenantsApi.switchTenant(tenantId)
      toast.success(`Switched to tenant '${tenantId}'`)
      await loadTenantInfo()
      await loadTenantsList()
      // Refresh page to update tenant context
      globalThis.window.location.reload()
    } catch (error: any) {
      toast.error(`Failed to switch tenant: ${error.message || "Unknown error"}`)
    } finally {
      setSwitching(false)
    }
  }

  const isDefaultTenant = currentTenant?.tenant_id === "default"

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Tenant Management</CardTitle>
          <CardDescription>
            Create or switch between tenants to customize rules without affecting the default configuration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Current Tenant Info */}
          {currentTenant && (
            <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-sm font-medium">Current Tenant</Label>
                  <p className="text-lg font-semibold">{currentTenant.tenant_id}</p>
                </div>
                {isDefaultTenant && (
                  <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded">
                    Default (Read-only)
                  </span>
                )}
              </div>
              {currentTenant.has_custom_rules && (
                <p className="text-sm text-muted-foreground">
                  ✓ Custom rules configured
                </p>
              )}
            </div>
          )}

          {isDefaultTenant && (
            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Note:</strong> You are using the default tenant. Rules cannot be modified here.
                Create a new tenant to customize your validation rules.
              </p>
            </div>
          )}

          {/* Create New Tenant */}
          <div className="space-y-4 border-t pt-4">
            <div>
              <Label className="text-base font-semibold">Create New Tenant</Label>
              <p className="text-sm text-muted-foreground mt-1">
                Create a new tenant with its own rule configuration
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tenant-id">Tenant ID</Label>
              <Input
                id="tenant-id"
                value={newTenantId}
                onChange={(e) => setNewTenantId(e.target.value)}
                placeholder="my_custom_tenant"
                disabled={creating}
              />
              <p className="text-xs text-muted-foreground">
                Use letters, numbers, underscores, and hyphens only (e.g., "acme_healthcare", "tenant-2024")
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="copy-rules"
                checked={copyFromDefault}
                onChange={(e) => setCopyFromDefault(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="copy-rules" className="text-sm font-normal cursor-pointer">
                Copy rules from default tenant (recommended)
              </Label>
            </div>

            <Button
              onClick={handleCreateTenant}
              disabled={creating || !newTenantId.trim()}
              className="w-full"
            >
              {creating ? "Creating..." : "Create Tenant"}
            </Button>
          </div>

          {/* Switch Tenant */}
          {tenants.length > 0 && (
            <div className="space-y-4 border-t pt-4">
              <div>
                <Label className="text-base font-semibold">Switch Tenant</Label>
                <p className="text-sm text-muted-foreground mt-1">
                  Switch to a different tenant to use its rules
                </p>
              </div>

              <Select
                value={currentTenant?.tenant_id || ""}
                onValueChange={handleSwitchTenant}
                disabled={switching}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a tenant" />
                </SelectTrigger>
                <SelectContent>
                  {tenants.map((tenant) => (
                    <SelectItem key={tenant.tenant_id} value={tenant.tenant_id}>
                      <div className="flex items-center gap-2">
                        <span>{tenant.tenant_id}</span>
                        {tenant.is_default && (
                          <span className="text-xs text-muted-foreground">(Default)</span>
                        )}
                        {tenant.is_current && (
                          <span className="text-xs text-blue-600">(Current)</span>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

