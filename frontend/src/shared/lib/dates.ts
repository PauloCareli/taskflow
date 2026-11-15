const formatter = new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeZone: 'UTC' })

export function formatDate(iso: string): string {
  return formatter.format(new Date(iso))
}

/** `YYYY-MM-DD` of an instant in UTC; the shape of a date input value. */
export function utcDateInput(date: Date): string {
  return date.toISOString().slice(0, 10)
}
