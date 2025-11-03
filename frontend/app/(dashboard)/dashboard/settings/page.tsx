import RulesManagement from "@/components/settings/rules-management"
import TenantManagement from "@/components/settings/tenant-management"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your account and validation preferences</p>
      </div>

      {/* Tenant Management - Must be first */}
      <TenantManagement />

      {/* Rules Management */}
      <RulesManagement />

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input id="name" defaultValue="Dr. Sarah Johnson" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" defaultValue="sarah.johnson@hospital.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="organization">Organization</Label>
            <Input id="organization" defaultValue="City General Hospital" />
          </div>
          <Button>Save Changes</Button>
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Validation Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="threshold">Error Threshold (%)</Label>
            <Input id="threshold" type="number" defaultValue="5" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="notifications">Email Notifications</Label>
            <Input id="notifications" type="email" defaultValue="alerts@hospital.com" />
          </div>
          <Button>Update Preferences</Button>
        </CardContent>
      </Card>
    </div>
  )
}
