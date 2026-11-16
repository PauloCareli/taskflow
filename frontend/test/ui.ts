import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

export async function openActions(card: HTMLElement) {
  await userEvent.click(within(card).getByRole('button', { name: /^actions for/i }))
  return screen.findByRole('menu')
}

export async function chooseAction(card: HTMLElement, name: RegExp | string) {
  const menu = await openActions(card)
  await userEvent.click(within(menu).getByRole('menuitem', { name }))
}

export async function chooseStatus(card: HTMLElement, label: string) {
  await userEvent.click(within(card).getByRole('button', { name: /change status/i }))
  await userEvent.click(await screen.findByRole('menuitem', { name: label }))
}
