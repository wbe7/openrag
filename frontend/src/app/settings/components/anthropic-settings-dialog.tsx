import { useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { FormProvider, useForm } from "react-hook-form";
import { toast } from "sonner";
import { useUpdateSettingsMutation } from "@/app/api/mutations/useUpdateSettingsMutation";
import { useGetSettingsQuery } from "@/app/api/queries/useGetSettingsQuery";
import type { ProviderHealthResponse } from "@/app/api/queries/useProviderHealthQuery";
import AnthropicLogo from "@/components/logo/anthropic-logo";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/contexts/auth-context";
import {
	AnthropicSettingsForm,
	type AnthropicSettingsFormData,
} from "./anthropic-settings-form";

const AnthropicSettingsDialog = ({
	open,
	setOpen,
}: {
	open: boolean;
	setOpen: (open: boolean) => void;
}) => {
	const { isAuthenticated, isNoAuthMode } = useAuth();
	const queryClient = useQueryClient();

	const { data: settings = {} } = useGetSettingsQuery({
		enabled: isAuthenticated || isNoAuthMode,
	});

	const isAnthropicConfigured = settings.provider?.model_provider === "anthropic";

	const methods = useForm<AnthropicSettingsFormData>({
		mode: "onSubmit",
		defaultValues: {
			apiKey: "",
			llmModel: isAnthropicConfigured ? settings.agent?.llm_model : "",
			embeddingModel: isAnthropicConfigured
				? settings.knowledge?.embedding_model
				: "",
		},
	});

	const { handleSubmit } = methods;

	const settingsMutation = useUpdateSettingsMutation({
		onSuccess: () => {
			// Update provider health cache to healthy since backend validated the setup
			const healthData: ProviderHealthResponse = {
				status: "healthy",
				message: "Provider is configured and working correctly",
				provider: "anthropic",
			};
			queryClient.setQueryData(["provider", "health"], healthData);

			toast.success("Anthropic settings updated successfully");
			setOpen(false);
		},
	});

	const onSubmit = (data: AnthropicSettingsFormData) => {
		const payload: {
			api_key?: string;
			model_provider: string;
			llm_model: string;
			embedding_model: string;
		} = {
			model_provider: "anthropic",
			llm_model: data.llmModel,
			embedding_model: data.embeddingModel,
		};

		// Only include api_key if a value was entered
		if (data.apiKey) {
			payload.api_key = data.apiKey;
		}

		// Submit the update
		settingsMutation.mutate(payload);
	};

	return (
		<Dialog open={open} onOpenChange={setOpen}>
			<DialogContent className="max-w-2xl">
				<FormProvider {...methods}>
					<form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
						<DialogHeader className="mb-2">
							<DialogTitle className="flex items-center gap-3">
								<div className="w-8 h-8 rounded flex items-center justify-center bg-white border">
									<AnthropicLogo className="text-black" />
								</div>
								Anthropic Setup
							</DialogTitle>
						</DialogHeader>

						<AnthropicSettingsForm isCurrentProvider={isAnthropicConfigured} />

						<AnimatePresence mode="wait">
							{settingsMutation.isError && (
								<motion.div
									key="error"
									initial={{ opacity: 0, y: 10 }}
									animate={{ opacity: 1, y: 0 }}
									exit={{ opacity: 0, y: -10 }}
								>
									<p className="rounded-lg border border-destructive p-4">
										{settingsMutation.error?.message}
									</p>
								</motion.div>
							)}
						</AnimatePresence>
						<DialogFooter className="mt-4">
							<Button
								variant="outline"
								type="button"
								onClick={() => setOpen(false)}
							>
								Cancel
							</Button>
							<Button type="submit" disabled={settingsMutation.isPending}>
								{settingsMutation.isPending ? "Saving..." : "Save"}
							</Button>
						</DialogFooter>
					</form>
				</FormProvider>
			</DialogContent>
		</Dialog>
	);
};

export default AnthropicSettingsDialog;
