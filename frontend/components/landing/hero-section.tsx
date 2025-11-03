import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles } from "lucide-react"

export function HeroSection() {
  return (
    <section className="relative overflow-hidden pt-32 pb-20">
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-primary/15 via-primary/8 to-transparent blur-3xl animate-[float_8s_ease-in-out_infinite]" />

        <div className="absolute top-1/3 right-0 h-[400px] w-[400px] translate-x-1/3 rounded-full bg-gradient-to-bl from-accent/12 via-accent/6 to-transparent blur-3xl animate-[float_10s_ease-in-out_infinite_2s]" />

        {/* Subtle dot pattern overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgb(0_0_0/0.05)_1px,transparent_0)] [background-size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_60%,transparent_100%)]" />

        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-primary/20 rounded-full animate-[pulse_3s_ease-in-out_infinite]" />
        <div className="absolute top-1/3 right-1/3 w-1.5 h-1.5 bg-accent/20 rounded-full animate-[pulse_4s_ease-in-out_infinite_1s]" />
        <div className="absolute bottom-1/3 left-1/3 w-1 h-1 bg-primary/15 rounded-full animate-[pulse_5s_ease-in-out_infinite_2s]" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center animate-[fadeInUp_0.8s_ease-out]">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/50 backdrop-blur-sm px-4 py-1.5 text-sm text-muted-foreground animate-[fadeInUp_0.8s_ease-out_0.2s_both]">
            <Sparkles className="h-4 w-4 text-primary animate-pulse" />
            <span>AI-Powered Claims Validation</span>
          </div>

          <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-foreground sm:text-6xl lg:text-7xl text-balance animate-[fadeInUp_0.8s_ease-out_0.4s_both]">
            Intelligent Healthcare{" "}
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent animate-[shimmer_3s_ease-in-out_infinite] bg-[length:200%_100%]">
              Claims Processing
            </span>
          </h1>

          <p className="mb-10 text-lg text-muted-foreground sm:text-xl leading-relaxed text-pretty max-w-2xl mx-auto animate-[fadeInUp_0.8s_ease-out_0.6s_both]">
            Transform your revenue cycle management with AI-driven validation. Detect errors, ensure compliance, and
            accelerate adjudication with precision.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row animate-[fadeInUp_0.8s_ease-out_0.8s_both]">
            <Button size="lg" className="gap-2 transition-transform hover:scale-105" asChild>
              <Link href="/signup">
                Start Validating
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" className="transition-transform hover:scale-105 bg-transparent" asChild>
              <Link href="#features">Learn More</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
