import { createSignal } from "solid-js"
import { useStore } from "@nanostores/solid"
import { authStore, setUser, clearUser } from "../stores/auth"

export default function Me() {
  const [error, setError] = createSignal<string | null>(null)
  const [loading, setLoading] = createSignal(false)

  const user = useStore(authStore)

  

  return (
    <div class="p-6">
      <h1 class="text-xl font-bold mb-4">Test /me endpoint</h1>

      {loading() && <p>Loading...</p>}

      {error() && (
        <p class="text-red-500">{error()}</p>
      )}

      {!user() && !loading() && (
        <p class="text-gray-500">No user loaded</p>
      )}

      {user() && (
        <pre class="bg-gray-100 p-4 rounded">
          {JSON.stringify(user(), null, 2)}
        </pre>
      )}
    </div>
  )
}