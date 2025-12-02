'use client'
import { useId } from "@/context/IdContext";

export default function Dashboard() {
  const { id, setId } = useId();
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <div>
          <p>Current ID: {id ?? "None"}</p>
          <button onClick={() => setId(123)}>Set ID to 123</button>
        </div>
    </div>
  );
}
