import { Brain, Shield, Zap, BarChart3, FileCheck, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"

const features = [
  {
    icon: Brain,
    title: "AI-Powered Analysis",
    description:
      "Advanced machine learning models validate claims against technical and medical rules with human-level accuracy.",
  },
  {
    icon: Shield,
    title: "Compliance Assurance",
    description: "Ensure every claim meets regulatory standards and payer requirements automatically.",
  },
  {
    icon: Zap,
    title: "Real-Time Processing",
    description: "Process thousands of claims in seconds with instant error detection and recommendations.",
  },
  {
    icon: BarChart3,
    title: "Visual Analytics",
    description: "Comprehensive dashboards with waterfall charts and detailed metrics for actionable insights.",
  },
  {
    icon: FileCheck,
    title: "Multi-Rule Validation",
    description: "Simultaneous technical and medical adjudication with detailed error explanations.",
  },
  {
    icon: Clock,
    title: "Faster Turnaround",
    description: "Reduce claim processing time by up to 80% with automated validation workflows.",
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 bg-muted/30 relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:3rem_3rem] opacity-50" />

      {/* Accent gradient */}
      <div className="absolute top-0 left-1/2 w-[600px] h-[300px] bg-primary/5 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl mb-4 text-balance">
            Everything you need for claims validation
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Powerful features designed for healthcare organizations of all sizes
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="border-border/50 bg-card/80 backdrop-blur-sm hover:shadow-lg hover:border-primary/20 transition-all duration-300"
            >
              <CardContent className="p-6">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-xl font-semibold text-card-foreground">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
