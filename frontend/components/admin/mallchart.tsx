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
  startDate: Date;
  endDate: Date;
}

type ChartData = {
  label: string;      // hour or day formatted nicely
  occupied_count: number;
};

function parseLocalISO(iso: string): Date {
  // const [date, time] = iso.split("T");
  // const [y, m, d] = date.split("-").map(Number);
  // const [h, min, s] = time.split(":").map(Number);
  //
  //
  // return new Date(y, m - 1, d, h, min, s);
  return new Date(iso + "Z");
}

export default function MallAnalyticsChart({ mallId, startDate, endDate }: Props) {
  const [data, setData] = useState<ChartData[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      try {
        const res = await getMallAnalyticsAnalyticsAggregationGet({
          query: {
            mall_id: mallId,
            start_date: startDate.toISOString().replace(/Z$/, ""),
            end_date: endDate.toISOString().replace(/Z$/, ""),
          },
        });

        // Automatically detect whether it's hourly or daily
        const frequency = res.data?.frequency;
        const rawAggregation = res.data?.aggregation;

        let mapped: ChartData[] = [];

        if (frequency === "hour") {
          mapped = (rawAggregation as HourlyAggregationItem[]).map((item) => ({
            label: new Date(parseLocalISO(item.hour)).toLocaleTimeString("en-SG", {
              hour: "2-digit",
              minute: "2-digit",
            }),
            occupied_count: item.occupied_count,
          }));
        } else if (frequency === "day") {
          mapped = (rawAggregation as DailyAggregationItem[]).map((item) => ({
            label: new Date(parseLocalISO(item.day)).toLocaleDateString("en-SG", {
              month: "short",
              day: "numeric",
            }),
            occupied_count: item.occupied_count,
          }));
        }

        setData(mapped);
      } catch (e) {
        console.error("Analytics fetch error:", e);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, [mallId, startDate, endDate]);

  if (isLoading) return <p>Loading analytics chart...</p>;

  return (
  <div>
    <h1 className="py-10 font-bold">Toilets Occupied in the last 24 hours</h1>
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

