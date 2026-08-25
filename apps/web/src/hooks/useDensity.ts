import { useEffect, useState } from "react";

type Density = "comfortable" | "compact";

const STORAGE_KEY = "local-ai-lab:preferences:v1:density";

function readInitialDensity(): Density {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "compact" ? "compact" : "comfortable";
  } catch {
    return "comfortable";
  }
}

function useDensity() {
  const [density, setDensity] = useState<Density>(readInitialDensity);

  useEffect(() => {
    document.documentElement.dataset.density = density;
    try {
      window.localStorage.setItem(STORAGE_KEY, density);
    } catch {
      // Device-local preference persistence is optional; rendering must still work.
    }
  }, [density]);

  return { density, setDensity };
}

export { STORAGE_KEY, useDensity };
export type { Density };
