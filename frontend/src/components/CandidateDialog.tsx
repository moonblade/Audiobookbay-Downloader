import { Button } from '@/components/ui/button';
import type { Candidate } from '@/types';

interface CandidateDialogProps {
  isOpen: boolean;
  candidates: Candidate[];
  onSelect: (candidate: Candidate) => void;
  onClose: () => void;
}

export function CandidateDialog({
  isOpen,
  candidates,
  onSelect,
  onClose,
}: CandidateDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-800 bg-opacity-75 flex justify-center items-center z-50 p-4">
      <div className="bg-gray-700 p-6 rounded-lg w-full max-w-md max-h-[80vh] overflow-y-auto">
        <h3 className="text-xl font-bold mb-4">Select a Candidate</h3>
        <div className="space-y-4">
          {candidates.map((candidate) => (
            <div
              key={candidate.id}
              className="flex items-center gap-4 p-4 bg-gray-600 rounded cursor-pointer hover:bg-gray-500"
              onClick={() => onSelect(candidate)}
            >
              {candidate.cover && (
                <img
                  src={candidate.cover}
                  alt="Cover"
                  className="w-16 h-16 object-cover rounded"
                />
              )}
              <div>
                <p className="font-bold">{candidate.album}</p>
                <p className="text-sm text-gray-400">{candidate.match}</p>
                <p className="text-sm text-gray-400">{candidate.artist}</p>
                <p className="text-sm text-gray-400">{candidate.length}</p>
              </div>
            </div>
          ))}
        </div>
        <Button
          onClick={onClose}
          className="mt-4 bg-gray-500 hover:bg-gray-600 text-white px-4 py-2"
        >
          Close
        </Button>
      </div>
    </div>
  );
}
