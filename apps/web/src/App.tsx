import { AppShell } from "./components/AppShell";
import { QueryProvider } from "./query/QueryProvider";

function App() {
  return (
    <QueryProvider>
      <AppShell />
    </QueryProvider>
  );
}

export { App };
