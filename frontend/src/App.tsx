import { A } from "@solidjs/router"

export default function App(props: any) {
  return (
    <div class="p-4">
      <nav class="flex gap-4 mb-4">
        <A href="/">Home</A>
        <A href="/about">About</A>
        <A href="/login">Login</A>
        <A href="/me">Me</A>
      </nav>

      {props.children}
    </div>
  )
}