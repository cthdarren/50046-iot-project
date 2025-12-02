"use client";

import { useEffect, useState } from "react";
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
  getToiletRollMeanAnalyticsToiletRollMeanGet,
  HourlyMeanPercentageItem,
  DailyMeanPercentageItem,
  MeanPercentageDto,
} from "../../app/services/analytics";
import { calculateDateRangeDuration } from "@/helpers/calculateDuration";

interface Props {
  mallId: number;
  toiletId: number;
  startDate: Date;
  endDate: Date;
}

type ChartData = {
  label: string;
  mean: number;
};

function parseUTCToLocal(iso: string): Date {
  return new Date(iso + "Z");
}

export default function ToiletRollMeanChart({
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
        const res = await getToiletRollMeanAnalyticsToiletRollMeanGet({
          query: {
            mall_id: mallId,
            toilet_id: toiletId,
            start_date: startDate.toISOString().replace(/Z$/, ""),
            end_date: endDate.toISOString().replace(/Z$/, ""),
          },
        });

        const payload: MeanPercentageDto = res.data!;
        const frequency = payload.frequency;
        const raw = payload.mean_percentages;

        let mapped: ChartData[] = [];

        if (frequency === "hour") {
          mapped = (raw as HourlyMeanPercentageItem[]).map((item) => ({
            label: parseUTCToLocal(item.hour).toLocaleTimeString("en-SG", {
              hour: "2-digit",
              minute: "2-digit",
            }),
            mean: item.mean_percentage ?? 0,
          }));
        } else {
          mapped = (raw as DailyMeanPercentageItem[]).map((item) => ({
            label: parseUTCToLocal(item.day).toLocaleDateString("en-SG", {
              month: "short",
              day: "numeric",
            }),
            mean: item.mean_percentage ?? 0,
          }));
        }

        setData(mapped);
      } catch (e) {
        console.error("Toilet roll mean analytics fetch error:", e);
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, [mallId, toiletId, startDate, endDate]);

  if (isLoading) return <p>Loading toilet roll mean analytics...</p>;

  return (
    <div>
      <h1 className="font-bold pb-10">
        Toilet Roll (Mean %) in the Last {calculateDateRangeDuration(startDate, endDate)}
      </h1>

      <ChartContainer
        config={{
          mean: {
            label: "Mean Toilet Roll (%)",
            color: "hsl(var(--chart-2))",
          },
        }}
        className="w-full h-[300px]"
      >
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis domain={[0, 100]} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey="mean"
            stroke="black"
            strokeWidth={2}
          />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
