"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useId } from "@/context/IdContext";

export default function Home() {
  const { id, setId } = useId();
  const [inputValue, setInputValue] = useState("");
  const router = useRouter();

  // Redirect immediately if ID already exists
  useEffect(() => {
    if (id !== null) {
      router.replace("/dashboard");
    }
  }, [id, router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const parsed = Number(inputValue);
    if (isNaN(parsed) || parsed <= 0) {
      alert("Please enter a valid numeric ID");
      return;
    }

    setId(parsed);
    router.push("/dashboard");
  };

  return (
    <main className="flex p-6">
      <h1 className="text-xl mb-4">Enter Your ID</h1>

      <form onSubmit={handleSubmit}>
        <input
          type="number"
          className="border p-2 rounded"
          placeholder="Enter ID"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />

        <button
          type="submit"
          className="ml-2 px-4 py-2 bg-blue-600 text-white rounded"
        >
          Continue
        </button>
      </form>
    </main>
  );
}

