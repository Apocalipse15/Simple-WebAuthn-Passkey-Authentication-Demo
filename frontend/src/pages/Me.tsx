import { createSignal, onMount } from "solid-js"
import { useStore } from "@nanostores/solid"
import { authStore, setUser, clearUser } from "../stores/auth"

export default function Me() {
  const [error, setError] = createSignal<string | null>(null)
  const [loading, setLoading] = createSignal(false)
  const [logoutLoading, setLogoutLoading] = createSignal(false)

  const user = useStore(authStore)

  const fetchMe = async () => {
    setLoading(true)
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        method: "GET",
        credentials: "include",
      })

      if (!res.ok) {
        clearUser()
        throw new Error("Not authenticated")
      }

      const data = await res.json()
      setUser(data)

    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    setLogoutLoading(true)
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        credentials: "include", 
      })

      if (!res.ok) {
        throw new Error("Logout failed")
      }

      clearUser()

    } catch (err: any) {
      setError(err.message)
    } finally {
      setLogoutLoading(false)
    }
  }

  onMount(() => {
    fetchMe()
  })

  return (
    <div class="p-6">
      <h1 class="text-xl font-bold mb-4">Test /me endpoint</h1>

      <div class="flex gap-2 mb-4">
        <button
          class="bg-blue-500 text-white px-4 py-2 rounded"
          onClick={fetchMe}
        >
          Refresh /me
        </button>

        <button
          class="bg-red-500 text-white px-4 py-2 rounded"
          onClick={handleLogout}
          disabled={logoutLoading()}
        >
          {logoutLoading() ? "Logging out..." : "Logout"}
        </button>
      </div>

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