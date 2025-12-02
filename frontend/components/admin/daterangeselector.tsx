"use client";

import { useEffect, useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Props {
  label: string;
  value: Date;
  onChange: (date: Date) => void;
}

export function DateTimePicker({ label, value, onChange }: Props) {
  const [open, setOpen] = useState(false);

  // Local temp state (only committed when clicking "Done")
  const [tempValue, setTempValue] = useState<Date>(value);

  // Sync local state when parent value changes
  useEffect(() => {
    setTempValue(value);
  }, [value]);

  const formatted = `${value.toLocaleDateString("en-SG")} ${value.toLocaleTimeString("en-SG", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;

  function updateTempTime(newTime: string) {
    const [h, m] = newTime.split(":").map(Number);
    const updated = new Date(tempValue);
    updated.setHours(h, m, 0, 0);
    setTempValue(updated);
  }

  function updateTempDate(day: Date) {
    const updated = new Date(day);
    updated.setHours(tempValue.getHours(), tempValue.getMinutes());
    setTempValue(updated);
  }

  function applyChanges() {
    onChange(tempValue); // ← Commit changes
    setOpen(false);
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="font-medium">{label}</label>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline">{formatted}</Button>
        </PopoverTrigger>

        <PopoverContent className="flex flex-col gap-4 p-4 w-auto">

          {/* DATE PICKER */}
          <Calendar
            mode="single"
            selected={tempValue}
            onSelect={(day) => {
              if (!day) return;
              updateTempDate(day);
            }}
          />

          {/* TIME INPUT */}
          <div className="flex items-center gap-2">
            <span className="text-sm opacity-70">Time:</span>
            <Input
              type="time"
              className="w-32"
              value={`${String(tempValue.getHours()).padStart(2, "0")}:${String(
                tempValue.getMinutes()
              ).padStart(2, "0")}`}
              onChange={(e) => updateTempTime(e.target.value)}
            />
          </div>

          {/* APPLY BUTTON */}
          <Button onClick={applyChanges} className="mt-2">Done</Button>
        </PopoverContent>
      </Popover>
    </div>
  );
}
