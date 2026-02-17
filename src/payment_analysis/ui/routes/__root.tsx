import * as React from 'react'
import { Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { ErrorBoundary } from 'react-error-boundary'
import { Toaster } from 'sonner'

export const Route = createRootRoute({
  component: RootComponent,
})

function RootErrorFallback({ error, resetErrorBoundary }: { error: unknown; resetErrorBoundary: () => void }) {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-4 p-8 text-center">
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 max-w-md">
        <h2 className="text-lg font-semibold text-destructive mb-2">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mb-4">
          {error instanceof Error ? error.message : 'An unexpected error occurred.'}
        </p>
        <button
          onClick={resetErrorBoundary}
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Try again
        </button>
      </div>
    </div>
  )
}

function RootComponent() {
  const router = useRouter()
  return (
    <React.Fragment>
      <ErrorBoundary
        FallbackComponent={RootErrorFallback}
        onReset={() => router.invalidate()}
      >
        <React.Suspense
          fallback={
            <div className="flex h-screen w-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          }
        >
          <Outlet />
        </React.Suspense>
      </ErrorBoundary>
      <Toaster position="bottom-right" richColors closeButton />
    </React.Fragment>
  )
}
