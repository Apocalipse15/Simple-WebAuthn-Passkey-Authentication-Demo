import { createSignal } from "solid-js"
import { setUser } from "../stores/auth"

export default function Login() {
  const [username, setUsername] = createSignal("")
  const [displayName, setDisplayName] = createSignal("")

  const [error, setError] = createSignal<string | null>(null)
  const [loginError, setLoginError] = createSignal<string | null>(null)

  const [loginLoading, setLoginLoading] = createSignal(false)

  function toUint8Array(input: any) {
    if (!input) {
      throw new Error("Missing WebAuthn binary field")
    }

    if (input instanceof Uint8Array) return input
    if (input instanceof ArrayBuffer) return new Uint8Array(input)

    if (typeof input === "string") {
      const binary = atob(input.replace(/-/g, "+").replace(/_/g, "/"))
      return Uint8Array.from(binary, c => c.charCodeAt(0))
    }

    throw new Error("Unsupported WebAuthn format: " + typeof input)
  }

  const handleCreateAccount = async (e: Event) => {
    e.preventDefault()
    setError(null)

    try {
      const res = await fetch("http://localhost:8000/auth/register/begin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username(),
          display_name: displayName(),
        }),
      })

      const options = await res.json()

      const publicKey = {
        ...options,
        challenge: toUint8Array(options.challenge),
        user: {
          ...options.user,
          id: toUint8Array(options.user.id),
        },
      }

      const credential = await navigator.credentials.create({
        publicKey,
      })

      console.log("WebAuthn credential:", credential)

      const res2 = await fetch("http://localhost:8000/auth/register/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username(),
          credential,
          device_name: "My Laptop",
        }),
      })

      console.log("Register complete:", await res2.json())
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleLogin = async (e: Event) => {
    e.preventDefault()

    setLoginLoading(true)
    setLoginError(null)

    try {
      const res = await fetch("http://localhost:8000/auth/authenticate/begin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username(),
        }),
      })

      console.log("Login options response:", res)
      
      const options = await res.json()

      const publicKey = {
        ...options,
        challenge: toUint8Array(options.challenge),
        allowCredentials: options.allowCredentials?.map((cred: any) => ({
          ...cred,
          id: toUint8Array(cred.id),
        })),
      }

      const assertion = await navigator.credentials.get({
        publicKey,
      })

      console.log("Login assertion:", assertion)

      const res2 = await fetch(
        "http://localhost:8000/auth/authenticate/complete",
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: username(),
            credential: assertion,
          }),
        }
      )

      const loginResult = await res2.json()
      console.log("Login success:", loginResult)
      setUser(loginResult)
    } catch (err: any) {
      setLoginError(err.message)
    } finally {
      setLoginLoading(false)
    }
  }

  return (
    <div class="min-h-screen flex items-center justify-center bg-gray-100">
      <div class="grid gap-6">

        {/* REGISTER */}
        <form
          onSubmit={handleCreateAccount}
          class="bg-white p-6 rounded-2xl shadow-md w-full max-w-sm"
        >
          <h1 class="text-xl font-bold mb-4">Create Account</h1>

          <input
            type="text"
            placeholder="Username"
            class="w-full mb-3 p-2 border rounded"
            value={username()}
            onInput={(e) => setUsername(e.currentTarget.value)}
            required
          />

          <input
            type="text"
            placeholder="Display Name"
            class="w-full mb-4 p-2 border rounded"
            value={displayName()}
            onInput={(e) => setDisplayName(e.currentTarget.value)}
            required
          />

          <button class="w-full bg-blue-500 text-white py-2 rounded">
            Create Account
          </button>

          {error() && (
            <p class="text-red-500 text-sm mt-2">{error()}</p>
          )}
        </form>

        {/* LOGIN */}
        <form
          onSubmit={handleLogin}
          class="bg-white p-6 rounded-2xl shadow-md w-full max-w-sm"
        >
          <h1 class="text-xl font-bold mb-4">Login</h1>

          <input
            type="text"
            placeholder="Username"
            class="w-full mb-4 p-2 border rounded"
            value={username()}
            onInput={(e) => setUsername(e.currentTarget.value)}
            required
          />

          <button
            class="w-full bg-green-500 text-white py-2 rounded"
            disabled={loginLoading()}
          >
            {loginLoading() ? "Logging in..." : "Login with Passkey"}
          </button>

          {loginError() && (
            <p class="text-red-500 text-sm mt-2">{loginError()}</p>
          )}
        </form>

      </div>
    </div>
  )
}