import { Component, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { failed: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  render() {
    if (this.state.failed) {
      return (
        <div role="alert" className="rounded-md border border-danger p-4 text-danger">
          <p className="font-semibold">Something went wrong.</p>
          <p>Reload the page to try again.</p>
        </div>
      )
    }
    return this.props.children
  }
}
