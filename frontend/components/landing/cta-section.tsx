import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function CTASection() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold tracking-tight text-foreground sm:text-4xl text-balance">
            Ready to transform your claims processing?
          </h2>
          <p className="mb-8 text-lg text-muted-foreground leading-relaxed">
            Join healthcare organizations using AI to streamline revenue cycle management
          </p>
          <Button size="lg" className="gap-2" asChild>
            <Link href="/login">
              Get Started Now
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
