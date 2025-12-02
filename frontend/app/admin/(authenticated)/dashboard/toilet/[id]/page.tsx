"use client";

import { useParams } from "next/navigation";
import { useId } from "@/context/IdContext";

import RealTimeCubicleOccupancyTable from "@/components/admin/toiletRealTimeOccupancy";
import { ToiletAnalyticsSection } from "@/components/admin/toiletanalyticssection";
import { DateTimePicker } from "@/components/admin/daterangeselector";

import { useState } from "react";

export default function ToiletDashboard() {
  const toiletId = Number(useParams().id);
  const { id: mallId } = useId();

  const [startDate, setStartDate] = useState(new Date("2025-12-02T00:00:00"));
  const [endDate, setEndDate] = useState(new Date("2025-12-03T00:00:00"));

  if (!mallId) return <div>No ID found. Please sign in again.</div>;

  return (
    <div className="flex min-h-screen items-start justify-center bg-zinc-50 dark:bg-black">
      <div className="w-full h-full flex flex-col gap-10 mt-10">

        {/* REALTIME STATUS */}
        <div>
          <h2 className="font-bold mb-5 text-2xl">Current Cubicle Occupancy</h2>
          <RealTimeCubicleOccupancyTable />
        </div>


        <div className="flex items-start">
        <h1 className="font-bold text-2xl flex-1">Analytics </h1>
        <div className="grid grid-cols-2 gap-6 max-w-xl">
          <DateTimePicker
            label="Start Date & Time"
            value={startDate}
            onChange={setStartDate}
          />

          <DateTimePicker
            label="End Date & Time"
            value={endDate}
            onChange={setEndDate}
          />
        </div>
        </div>

        <ToiletAnalyticsSection
          mallId={mallId}
          toiletId={toiletId}
          startDate={startDate}
          endDate={endDate}
        />
      </div>
    </div>
  );
}
