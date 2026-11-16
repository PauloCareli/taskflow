import { zodResolver } from '@hookform/resolvers/zod'
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { utcDateInput } from '../../../shared/lib/dates'
import { Button } from '../../../shared/ui/Button'
import { Dialog } from '../../../shared/ui/Dialog'
import { SelectField } from '../../../shared/ui/SelectField'
import { TextAreaField } from '../../../shared/ui/TextAreaField'
import { TextField } from '../../../shared/ui/TextField'
import { useAssignTask, useCreateTask, useUpdateTask } from '../hooks/useTaskMutations'
import type { TaskChanges } from '../api/tasksApi'
import { useUsers } from '../../users/hooks/useUsers'
import { taskFormSchema, type Task, type TaskFormValues } from '../schemas/taskSchemas'

type Props = { task?: Task; onClose: () => void }

const endOfDay = (date: string) => `${date}T23:59:59Z`

export function TaskFormDialog({ task, onClose }: Props) {
  const editing = task !== undefined
  const [formError, setFormError] = useState<string | null>(null)
  const users = useUsers()
  const create = useCreateTask()
  const update = useUpdateTask()
  const assign = useAssignTask()

  const defaults = useMemo<TaskFormValues>(
    () => ({
      title: task?.title ?? '',
      description: task?.description ?? '',
      dueDate: task?.due_date ? task.due_date.slice(0, 10) : '',
      assigneeId: task?.assignee?.id ?? '',
    }),
    [task],
  )
  const schema = useMemo(
    () => taskFormSchema({ rejectPastDueDate: !editing, today: utcDateInput(new Date()) }),
    [editing],
  )
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormValues>({ resolver: zodResolver(schema), defaultValues: defaults })

  const people = users.data ?? (task?.assignee ? [task.assignee] : [])

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null)
    try {
      if (!task) {
        await create.mutateAsync({
          title: values.title,
          ...(values.description && { description: values.description }),
          ...(values.dueDate && { due_date: endOfDay(values.dueDate) }),
          ...(values.assigneeId && { assignee_id: values.assigneeId }),
        })
      } else {
        const changes: TaskChanges = {}
        if (values.title !== defaults.title) changes.title = values.title
        if (values.description !== defaults.description) changes.description = values.description
        if (values.dueDate !== defaults.dueDate) {
          changes.due_date = values.dueDate ? endOfDay(values.dueDate) : null
        }
        if (Object.keys(changes).length > 0) await update.mutateAsync({ id: task.id, changes })
        if (values.assigneeId !== defaults.assigneeId) {
          await assign.mutateAsync({ id: task.id, assigneeId: values.assigneeId || null })
        }
      }
      onClose()
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not save the task')
    }
  })

  return (
    <Dialog title={editing ? 'Edit task' : 'New task'} onClose={onClose}>
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {formError ? (
          <p role="alert" className="text-sm text-danger">
            {formError}
          </p>
        ) : null}
        <TextField label="Title" error={errors.title?.message} {...register('title')} />
        <TextAreaField
          label="Description"
          error={errors.description?.message}
          {...register('description')}
        />
        <TextField
          label="Due date"
          type="date"
          error={errors.dueDate?.message}
          {...register('dueDate')}
        />
        <SelectField label="Assignee" {...register('assigneeId')}>
          <option value="">Unassigned</option>
          {people.map((person) => (
            <option key={person.id} value={person.id}>
              {person.name}
            </option>
          ))}
        </SelectField>
        {users.isError ? (
          <p className="text-sm text-fg-muted">Could not load the list of users.</p>
        ) : null}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {editing ? 'Save changes' : 'Create task'}
          </Button>
        </div>
      </form>
    </Dialog>
  )
}
