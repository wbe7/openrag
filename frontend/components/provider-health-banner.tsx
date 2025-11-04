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
  const { data: health, isLoading, error, isError } = useProviderHealthQuery();

  const isHealthy = health?.status === "healthy" && !isError;
  const isUnhealthy =
    health?.status === "unhealthy" || health?.status === "error" || isError;

  return {
    health,
    isLoading,
    error,
    isError,
    isHealthy,
    isUnhealthy,
    provider: health?.provider,
  };
}

export function ProviderHealthBanner({ className }: ProviderHealthBannerProps) {
  const { isLoading, isHealthy, isUnhealthy, error, provider } =
    useProviderHealth();
  const router = useRouter();

  // Only show banner when provider is unhealthy
  if (isLoading || isHealthy) {
    return null;
  }

  if (isUnhealthy) {
    const errorMessage = error?.message || "Provider validation failed";
    const settingsUrl = provider ? `/settings?setup=${provider}` : "/settings";

    return (
      <Banner
        className={cn(
          "bg-red-50 dark:bg-red-950 text-foreground border-accent-red border-b w-full",
          className
        )}
      >
        <BannerIcon
          className="text-accent-red-foreground"
          icon={AlertTriangle}
        />
        <BannerTitle className="font-medium">{errorMessage}</BannerTitle>
        <Button size="sm" onClick={() => router.push(settingsUrl)}>
          Fix Setup
        </Button>
      </Banner>
    );
  }

  return null;
}
