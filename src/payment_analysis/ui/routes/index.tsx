import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/apx/navbar";
import Logo from "@/components/apx/logo";
import { motion } from "motion/react";
import { BarChart3, Rocket, ArrowRight, Sparkles, Shield, Zap } from "lucide-react";
import { BubbleBackground } from "@/components/backgrounds/bubble";

export const Route = createFileRoute("/")({
  component: () => <Index />,
});

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0 },
};

function Index() {
  return (
    <div className="relative h-screen w-screen overflow-hidden flex flex-col bg-background">
      <Navbar leftContent={<Logo to="/" showText />} />

      <main className="flex-1 grid md:grid-cols-2 min-h-0">
        <BubbleBackground interactive />

        <div className="relative flex flex-col items-center justify-center p-8 md:p-12 lg:p-16 border-l border-border/50 bg-gradient-to-b from-background/98 via-background/95 to-background/98 backdrop-blur-md">
          <motion.div
            className="max-w-xl w-full space-y-8 text-center"
            variants={container}
            initial="hidden"
            animate="show"
          >
            <motion.div
              variants={item}
              className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary shadow-sm"
            >
              <Sparkles className="h-4 w-4" />
              Payment Approval Intelligence · Getnet
            </motion.div>

            <motion.h1
              variants={item}
              className="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold tracking-tight text-foreground leading-[1.1] font-heading"
            >
              Turn declines
              <br />
              <span className="bg-gradient-to-r from-primary to-emerald-500 bg-clip-text text-transparent">
                into revenue.
              </span>
            </motion.h1>

            <motion.p
              variants={item}
              className="text-lg md:text-xl text-muted-foreground max-w-md mx-auto leading-relaxed"
            >
              Real-time analytics, ML models, and AI agents to maximize authorization rates and grow conversion — built for payment leaders.
            </motion.p>

            <motion.div
              variants={item}
              className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-2"
            >
              <Button
                size="lg"
                className="gap-2 min-w-[220px] h-14 text-base font-semibold shadow-xl shadow-primary/25 hover:shadow-primary/30 transition-all duration-300 hover:scale-[1.02]"
                asChild
              >
                <Link to="/dashboard">
                  <BarChart3 className="h-5 w-5" />
                  View performance
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="gap-2 min-w-[220px] h-14 text-base font-medium border-2"
                asChild
              >
                <Link to="/setup">
                  <Rocket className="h-5 w-5" />
                  Setup & run
                </Link>
              </Button>
            </motion.div>

            <motion.div
              variants={item}
              className="flex flex-wrap justify-center gap-6 pt-6 text-sm text-muted-foreground"
            >
              <span className="inline-flex items-center gap-1.5">
                <Shield className="h-4 w-4 text-primary/80" />
                Smart routing & retry
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Zap className="h-4 w-4 text-primary/80" />
                Live dashboards
              </span>
            </motion.div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
