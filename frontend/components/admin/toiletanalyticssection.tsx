"use client";

import ToiletAnalyticsChart from "@/components/admin/toiletchart";
import ToiletRollMeanChart from "@/components/admin/toiletrollmeanchart";

interface Props {
  mallId: number;
  toiletId: number;
  startDate: Date;
  endDate: Date;
}

export function ToiletAnalyticsSection({ mallId, toiletId, startDate, endDate }: Props) {
  return (
    <div className="flex flex-col gap-20 mt-10">
      <ToiletAnalyticsChart
        mallId={mallId}
        toiletId={toiletId}
        startDate={startDate}
        endDate={endDate}
      />

      <ToiletRollMeanChart
        mallId={mallId}
        toiletId={toiletId}
        startDate={startDate}
        endDate={endDate}
      />
    </div>
  );
}
