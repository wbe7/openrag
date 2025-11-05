"use client";

import { AlertTriangle } from "lucide-react";
import { Banner, BannerIcon, BannerTitle } from "@/components/ui/banner";
import { cn } from "@/lib/utils";
import { useProviderHealthQuery } from "@/src/app/api/queries/useProviderHealthQuery";
import { Button } from "./ui/button";
import { useRouter } from "next/navigation";
import AnimatedProcessingIcon from "@/components/ui/animated-processing-icon";

interface ProviderHealthBannerProps {
  className?: string;
}

// Custom hook to check provider health status
export function useProviderHealth() {
  const {
    data: health,
    isLoading,
    isFetching,
    error,
    isError,
  } = useProviderHealthQuery();

  const isHealthy = health?.status === "healthy" && !isError;
  const isUnhealthy =
    health?.status === "unhealthy" || health?.status === "error" || isError;

  return {
    health,
    isLoading,
    isFetching,
    error,
    isError,
    isHealthy,
    isUnhealthy,
    provider: health?.provider,
  };
}

export function ProviderHealthBanner({ className }: ProviderHealthBannerProps) {
  const { isFetching, isLoading, isHealthy, error, provider } =
    useProviderHealth();
  const router = useRouter();

  if (!isHealthy && !isLoading) {
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
        <BannerTitle className="font-medium flex items-center gap-2">
          {errorMessage}
          {isFetching && (
            <>
              <AnimatedProcessingIcon className="text-current shrink-0 h-4 w-4" />
              <span className="text-muted-foreground">Revalidating...</span>
            </>
          )}
        </BannerTitle>
        <Button size="sm" onClick={() => router.push(settingsUrl)}>
          Fix Setup
        </Button>
      </Banner>
    );
  }

  return null;
}
