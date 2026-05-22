import { atom } from "nanostores"

export type User = {
  id: string
  username: string
  display_name: string
  is_active: boolean
  is_verified: boolean
} | null

export const authStore = atom<User>(null)

// helper functions
export function setUser(user: User) {
  authStore.set(user)
}

export function clearUser() {
  authStore.set(null)
}