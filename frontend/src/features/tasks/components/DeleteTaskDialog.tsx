import { Button } from '../../../shared/ui/Button'
import { Dialog } from '../../../shared/ui/Dialog'
import type { Task } from '../schemas/taskSchemas'

type Props = { task: Task; pending: boolean; onConfirm: () => void; onCancel: () => void }

export function DeleteTaskDialog({ task, pending, onConfirm, onCancel }: Props) {
  return (
    <Dialog title="Delete task?" role="alertdialog" onClose={onCancel}>
      <p className="text-sm">“{task.title}” will be permanently deleted. This cannot be undone.</p>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="danger" disabled={pending} onClick={onConfirm}>
          Delete
        </Button>
      </div>
    </Dialog>
  )
}
