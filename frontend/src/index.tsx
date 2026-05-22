import { render } from "solid-js/web"
import { Router, Route } from "@solidjs/router"
import { QueryClient, QueryClientProvider } from "@tanstack/solid-query"

import App from "./App"
import Home from "./pages/Home"
import Login from "./pages/Login"
import About from "./pages/About"
import Me from "./pages/Me"

const queryClient = new QueryClient()

render(() => (
  <QueryClientProvider client={queryClient}>
    <Router root={App}>
      <Route path="/" component={Home} />
      <Route path="/about" component={About} />
      <Route path="/login" component={Login} />
      <Route path="/me" component={Me} />
    </Router>
  </QueryClientProvider>
), document.getElementById("root")!)