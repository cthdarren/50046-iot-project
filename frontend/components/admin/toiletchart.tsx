"use client";

import { useEffect, useState } from "react";
import { getMallAnalyticsAnalyticsAggregationGet } from "../../app/services/analytics";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";

import {
  AggregationDto,
  HourlyAggregationItem,
  DailyAggregationItem,
} from "../../app/services/analytics";

interface Props {
  mallId: number;
  toiletId: number;
  startDate: Date;
  endDate: Date;
}

type ChartData = {
  label: string;
  occupied_count: number;
};

function parseUTCToLocal(iso: string): Date {
  return new Date(iso + "Z");
}

export default function ToiletAnalyticsChart({
  mallId,
  toiletId,
  startDate,
  endDate,
}: Props) {
  const [data, setData] = useState<ChartData[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      try {
        const res = await getMallAnalyticsAnalyticsAggregationGet({
          query: {
            mall_id: mallId,
            toilet_id: toiletId,
            start_date: startDate.toISOString().replace(/Z$/, ""),
            end_date: endDate.toISOString().replace(/Z$/, ""),
          },
        });

        const frequency = res.data?.frequency;
        const rawAggregation = res.data?.aggregation;

        let mapped: ChartData[] = [];

        if (frequency === "hour") {
          mapped = (rawAggregation as HourlyAggregationItem[]).map((item) => ({
            label: parseUTCToLocal(item.hour).toLocaleTimeString("en-SG", {
              hour: "2-digit",
              minute: "2-digit",
            }),
            occupied_count: item.occupied_count,
          }));
        } else if (frequency === "day") {
          mapped = (rawAggregation as DailyAggregationItem[]).map((item) => ({
            label: parseUTCToLocal(item.day).toLocaleDateString("en-SG", {
              month: "short",
              day: "numeric",
            }),
            occupied_count: item.occupied_count,
          }));
        }

        setData(mapped);
      } catch (e) {
        console.error("Toilet analytics fetch error:", e);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, [mallId, toiletId, startDate, endDate]);

  if (isLoading) return <p>Loading toilet analytics...</p>;

  return (
    <div>
      <h1 className="py-10 font-bold">Cubicles Occupied in the last 24 hours</h1>

      <ChartContainer
        config={{
          occupied_count: {
            label: "Occupied Count",
            color: "hsl(var(--chart-1))",
          },
        }}
        className="w-full h-[300px]"
      >
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey="occupied_count"
            stroke="black"
            strokeWidth={2}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
