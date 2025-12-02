"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useId } from "@/context/IdContext";
import { usePolling } from "@/hooks/use-polling";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

import {
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  CubicleDto,
} from "@/app/services/availability";

interface ParsedCubicle {
  id: number;
  occupied: boolean;
  toilet_roll_percentage: number | null;
}

export default function RealTimeCubicleOccupancyTable() {
  const { id: mallId } = useId();
  const params = useParams();
  const toiletId = Number(params.id);

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ParsedCubicle[]>([]);

  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = React.useState({});

  // ----------------------------
  // TABLE COLUMNS
  // ----------------------------
  const columns: ColumnDef<ParsedCubicle>[] = [
    {
      accessorKey: "id",
      header: "Cubicle ID",
      cell: ({ row }) => <div>{row.getValue("id")}</div>,
    },
    {
      accessorKey: "occupied",
      header: "Occupied",
      cell: ({ row }) => {
        const occ = row.getValue("occupied") as boolean;
        return (
          <span className={`font-medium ${occ ? "text-red-600" : "text-green-600"}`}>
            {occ ? "Occupied" : "Vacant"}
          </span>
        );
      },
    },
{
  accessorKey: "toilet_roll_percentage",
  header: "Toilet Roll",
  cell: ({ row }) => {
    const value = row.getValue("toilet_roll_percentage") as number | null;

    if (value === null || value === undefined) {
      return <div>N/A</div>;
    }

    let color = "text-black"; // default

    if (value < 15) {
      color = "text-red-600 font-bold";
    } else if (value < 40) {
      color = "text-orange-500 font-semibold";
    }

    return <div className={color}>{value}%</div>;
  },
}  ];

  // ----------------------------
  // REACT TABLE SETUP
  // ----------------------------
  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
  });

  // ----------------------------
  // FETCH CUBICLES
  // ----------------------------
  async function fetchCubicleOccupancy() {
    if (!mallId || !toiletId) return;

    try {
      const res = await getCubiclesMallsMallIdToiletsToiletIdCubiclesGet({
        path: { mall_id: mallId, toilet_id: toiletId },
      });

      const cubicles: CubicleDto[] = res.data?.cubicles ?? [];

      const parsed: ParsedCubicle[] = cubicles.map((c) => ({
        id: c.id,
        occupied: c.occupied ?? false,
        toilet_roll_percentage: c.toilet_roll_percentage ?? null,
      }));

      setData(parsed);
    } catch (err) {
      console.error("Failed to fetch cubicle occupancy", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCubicleOccupancy();
  }, [mallId, toiletId]);

  usePolling(fetchCubicleOccupancy);

  // ----------------------------
  // RENDER
  // ----------------------------
  return (
    <>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>

          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No cubicles found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end space-x-2 py-4">
        <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
          Previous
        </Button>
        <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
          Next
        </Button>
      </div>
    </>
  );
}

