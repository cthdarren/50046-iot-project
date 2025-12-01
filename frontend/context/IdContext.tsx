"use client";

import { createContext, useContext, useState, ReactNode } from "react";

type IdContextType = {
  id: number | null;
  setId: (id: number) => void;
};

const IdContext = createContext<IdContextType | undefined>(undefined);

export function IdProvider({ children }: { children: ReactNode }) {
  const [id, setId] = useState<number | null>(null);

  return (
    <IdContext.Provider value={{ id, setId }}>
      {children}
    </IdContext.Provider>
  );
}

export function useId() {
  const ctx = useContext(IdContext);
  if (!ctx) {
    throw new Error("useId must be used inside an IdProvider");
  }
  return ctx;
}

