'use client'
import { useId } from "@/context/IdContext";

export default function Dashboard() {
  const { id, setId } = useId();
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <div>
        </div>
    </div>
  );
}
