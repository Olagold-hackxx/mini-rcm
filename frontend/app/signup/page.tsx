import { SignupForm } from "@/components/auth/signup-form"
import { Activity } from "lucide-react"
import Link from "next/link"

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Activity className="h-6 w-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-semibold text-foreground">MediClaim AI</span>
          </Link>
          <h1 className="text-3xl font-bold text-foreground mb-2">Get started</h1>
          <p className="text-muted-foreground">Create an account to access the validation platform</p>
        </div>
        <SignupForm />
      </div>
    </div>
  )
}

