"use client";

import { useEffect, useState } from "react";
import { useId } from "@/context/IdContext";
import {
    CubicleDto,
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  getToiletsMallsMallIdToiletsGet,
} from "@/app/services/availability";

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
  VisibilityState,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { MallToiletOccupancy, ParsedToilet, Toilet } from "../../../models/models";
import { usePolling } from "@/hooks/use-polling";
import { getMallAnalyticsAnalyticsAggregationGet } from "@/app/services/analytics";
import MallAnalyticsChart from "@/components/admin/mallchart";
import RealTimeOccupancyTable from "@/components/admin/mallRealTimeOccupancy";



export default function Dashboard() {
  const { id } = useId();


  if (!id) return <div>No ID found. Please sign in again.</div>;
  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
    <div className="h-screen w-10/12 gap-10 flex flex-col">
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

