"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useId } from "@/context/IdContext";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { client } from "./services/availability/client.gen";

client.setConfig({
  baseUrl: 'http://iot-backend-alb-227826614.ap-southeast-1.elb.amazonaws.com',
});

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
    <div className="flex w-full h-full justify-center items-center">
    <div className="flex flex-col -mt-40">
      <h1 className="text-xl mb-4">Enter Mall ID</h1>

      <form className="flex" onSubmit={handleSubmit}>
        <Input
          type="number"
          className="border p-2 rounded"
          placeholder="Enter Mall ID"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
        />

        <Button
          type="submit"
          className="ml-2 px-4 py-2 bg-blue-600 text-white rounded"
        >
          Continue
        </Button>
      </form>
      </div>
    </div>
  );
}

