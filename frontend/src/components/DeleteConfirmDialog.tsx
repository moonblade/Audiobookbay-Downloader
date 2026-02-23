import { Button } from '@/components/ui/button';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirmDialog({
  isOpen,
  isDeleting,
  onConfirm,
  onCancel,
}: DeleteConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50 p-4"
      onClick={onCancel}
    >
      <div
        className="bg-gray-700 p-6 rounded-lg w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-xl font-bold mb-4">Confirm Delete</h3>
        <p>Are you sure you want to delete this torrent and its data?</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button
            onClick={onConfirm}
            disabled={isDeleting}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {isDeleting && (
              <span className="animate-spin border-2 border-white border-t-transparent rounded-full w-4 h-4 mr-1" />
            )}
            Delete
          </Button>
          <Button
            onClick={onCancel}
            variant="secondary"
            className="bg-gray-500 hover:bg-gray-600 text-white"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
