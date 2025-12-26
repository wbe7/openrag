"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useGetGroupsQuery } from "@/app/api/queries/useGetGroupsQuery";
import { useCreateGroupMutation } from "@/app/api/mutations/useCreateGroupMutation";
import { useDeleteGroupMutation } from "@/app/api/mutations/useDeleteGroupMutation";
import { Plus, Trash2, Loader2, Users } from "lucide-react";
import { toast } from "sonner";

interface ManageGroupsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ManageGroupsModal({
  open,
  onOpenChange,
}: ManageGroupsModalProps) {
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDescription, setNewGroupDescription] = useState("");

  const { data: groupsData, isLoading: groupsLoading } = useGetGroupsQuery({
    enabled: open,
  });

  const createGroupMutation = useCreateGroupMutation({
    onSuccess: () => {
      setNewGroupName("");
      setNewGroupDescription("");
      toast.success("Group created successfully");
    },
    onError: (error) => {
      toast.error("Failed to create group", { description: error.message });
    },
  });

  const deleteGroupMutation = useDeleteGroupMutation({
    onSuccess: () => {
      toast.success("Group deleted successfully");
    },
    onError: (error) => {
      toast.error("Failed to delete group", { description: error.message });
    },
  });

  const handleCreateGroup = () => {
    if (!newGroupName.trim()) {
      toast.error("Please enter a group name");
      return;
    }
    createGroupMutation.mutate({
      name: newGroupName.trim(),
      description: newGroupDescription.trim(),
    });
  };

  const handleDeleteGroup = (groupId: string, groupName: string) => {
    if (confirm(`Are you sure you want to delete the group "${groupName}"?`)) {
      deleteGroupMutation.mutate({ group_id: groupId });
    }
  };

  const groups = groupsData?.groups || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Manage User Groups</DialogTitle>
          <DialogDescription>
            Create and manage user groups for access control. Groups can be
            assigned to API keys to restrict document access.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Add new group section */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Create New Group</label>
            <div className="flex gap-2">
              <Input
                placeholder="Group name"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleCreateGroup();
                  }
                }}
                className="flex-1"
              />
              <Button
                onClick={handleCreateGroup}
                disabled={
                  createGroupMutation.isPending || !newGroupName.trim()
                }
                size="sm"
              >
                {createGroupMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
              </Button>
            </div>
            <Input
              placeholder="Description (optional)"
              value={newGroupDescription}
              onChange={(e) => setNewGroupDescription(e.target.value)}
              className="text-sm"
            />
          </div>

          {/* Existing groups list */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Existing Groups</label>
            {groupsLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : groups.length > 0 ? (
              <div className="border rounded-lg divide-y max-h-48 overflow-y-auto">
                {groups.map((group) => (
                  <div
                    key={group.group_id}
                    className="flex items-center justify-between px-3 py-2 hover:bg-muted/50"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {group.name}
                      </p>
                      {group.description && (
                        <p className="text-xs text-muted-foreground truncate">
                          {group.description}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={() =>
                        handleDeleteGroup(group.group_id, group.name)
                      }
                      disabled={deleteGroupMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 border rounded-lg">
                <Users className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground">
                  No groups yet. Create one above.
                </p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

