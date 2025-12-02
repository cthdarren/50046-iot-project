"use client";

import { useId } from "@/context/IdContext";
import RealTimeOccupancyTable from "@/components/admin/mallRealTimeOccupancy";
import ToiletAnalyticsChart from "@/components/admin/toiletchart";
import { useParams } from "next/navigation";
import RealTimeCubicleOccupancyTable from "@/components/admin/toiletRealTimeOccupancy";



export default function ToiletDashboard() {
  const toiletId = useParams().id?.toString()
  const { id } = useId();


  if (!id) return <div>No ID found. Please sign in again.</div>;
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
    <div className="h-screen w-10/12 gap-10 flex flex-col">
    <ToiletAnalyticsChart
      mallId={id}
      toiletId={parseInt(toiletId || "1")}
      startDate={new Date("2025-12-02T00:00:00")}
      endDate={new Date("2025-12-03T00:00:00")}
    />

    <RealTimeCubicleOccupancyTable/>

    </div>
    </div>
  )
}

