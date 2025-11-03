"use client";

import { AlertTriangle } from "lucide-react";
import { Banner, BannerIcon, BannerTitle } from "@/components/ui/banner";
import { cn } from "@/lib/utils";
import { useProviderHealthQuery } from "@/src/app/api/queries/useProviderHealthQuery";
import { Button } from "./ui/button";
import { useRouter } from "next/navigation";

interface ProviderHealthBannerProps {
  className?: string;
}

// Custom hook to check provider health status
export function useProviderHealth() {
  const { data: health, isLoading, isError } = useProviderHealthQuery();

  const isHealthy = health?.status === "healthy" && !isError;
  const isUnhealthy =
    health?.status === "unhealthy" || health?.status === "error" || isError;

  return {
    health,
    isLoading,
    isError,
    isHealthy,
    isUnhealthy,
  };
}

export function ProviderHealthBanner({ className }: ProviderHealthBannerProps) {
  const { health, isLoading, isHealthy, isUnhealthy } = useProviderHealth();
  const router = useRouter();

  // Only show banner when provider is unhealthy
  if (isLoading || isHealthy) {
    return null;
  }

  if (isUnhealthy) {
    const providerName = health?.provider || "Model provider";
    const message = health?.message || "Provider validation failed";

    return (
      <Banner
        className={cn(
          "bg-red-50 text-foreground dark:bg-red-950 border-accent-red border-b",
          className
        )}
      >
        <BannerIcon
          className="text-accent-red-foreground"
          icon={AlertTriangle}
        />
        <BannerTitle className="font-medium">
          {providerName} configuration issue: {message}
        </BannerTitle>
        <Button onClick={() => router.push("/settings")}>Fix Setup</Button>
      </Banner>
    );
  }

  return null;
}
