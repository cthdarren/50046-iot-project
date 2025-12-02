"use client";

import { createContext, useContext, useEffect, useState } from "react";

type IdContextType = {
  id: number | null;
  setId: (id: number) => void;
  loaded: boolean;
};

const IdContext = createContext<IdContextType | undefined>(undefined);

export function IdProvider({ children }: { children: React.ReactNode }) {
  const [id, setIdState] = useState<number | null>(null); 
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("id");
    if (stored) setIdState(Number(stored));
    setLoaded(true);
  }, []);

  const setId = (value: number) => {
    setIdState(value);
    localStorage.setItem("id", String(value));
  };

  return (
    <IdContext.Provider value={{ id, setId, loaded }}>
      {children}
    </IdContext.Provider>
  );
}

export function useId() {
  const ctx = useContext(IdContext);
  if (!ctx) throw new Error("useId must be used inside an IdProvider");
  return ctx;
}

