"use client";

import { useId } from "@/context/IdContext";
import MallAnalyticsChart from "@/components/admin/mallchart";
import RealTimeOccupancyTable from "@/components/admin/mallRealTimeOccupancy";



export default function Dashboard() {
  const { id } = useId();


  if (!id) return <div>No ID found. Please sign in again.</div>;
  return (
    <div className="flex min-h-screen items-center bg-zinc-50 font-sans dark:bg-black">
    <div className="h-screen w-full gap-10 flex flex-col">
    <MallAnalyticsChart
      mallId={id}
      startDate={new Date("2025-12-02T00:00:00")}
      endDate={new Date("2025-12-03T00:00:00")}
    />

    <RealTimeOccupancyTable/>

    </div>
    </div>
  )
}

