"use client";

import { useEffect, useState } from "react";
import { useId } from "@/context/IdContext";
import {
    CubicleDto,
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  getToiletsMallsMallIdToiletsGet,
  ToiletDto
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
import { ArrowUpDown, ChevronDown, MoreHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { MallToiletOccupancy, ParsedToilet, Toilet } from "../../../models/models";

function parseMallToiletOccupancy(
  mall: MallToiletOccupancy
): ParsedToilet[] {
  return mall.toilets.map((t) => ({
    name: t.description,
    level: t.level,
    occupancy: `${t.occupied_count}/${t.total_cubicles}`,
  }));
}

// const toiletdata: MallToiletOccupancy = {
//     mall_id: 1,
//     toilets: [
//       {
//         id: 101,
//         level: "B1",
//         gender: "Male",
//         description: "Near Food Court",
//         mall_id: 1,
//         cubicles: [
//           { id: 1, toilet_id: 101, occupied: true, toilet_roll_percentage: 45 },
//           { id: 2, toilet_id: 101, occupied: false, toilet_roll_percentage: 80 },
//           { id: 3, toilet_id: 101, occupied: true, toilet_roll_percentage: 60 },
//         ],
//         total_cubicles: 3,
//         occupied_count: 2,
//         occupancy_percentage: 66.7,
//       },
//       {
//         id: 102,
//         level: "L1",
//         gender: "Female",
//         description: "Next to Zara",
//         mall_id: 1,
//         cubicles: [
//           { id: 4, toilet_id: 102, occupied: false, toilet_roll_percentage: 90 },
//           { id: 5, toilet_id: 102, occupied: false, toilet_roll_percentage: 70 },
//           { id: 6, toilet_id: 102, occupied: true, toilet_roll_percentage: 50 },
//           { id: 7, toilet_id: 102, occupied: false, toilet_roll_percentage: 30 },
//         ],
//         total_cubicles: 4,
//         occupied_count: 1,
//         occupancy_percentage: 25,
//       },
//     ],
//   }

export const columns: ColumnDef<ParsedToilet>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <div className="capitalize">{row.getValue("name")}</div>
    ),
  },
  {
    accessorKey: "level",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          className="p-0!"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
            Level
          <ArrowUpDown />
        </Button>
      )
    },
    cell: ({ row }) => <div className="uppercase">{row.getValue("level")}</div>,
  },
  {
    accessorKey: "occupancy",
    header: () => <div className="text-right">Occupancy</div>,
    cell: ({ row }) => {
      return <div className="text-right font-medium">{row.getValue("occupancy")}</div>
    },
  },
  {
    accessorKey: "actions",
    header: () => <div className="text-right">Actions</div>,
    id: "actions",
    enableHiding: false,
    cell: ({ row }) => {
      return (
        <div className="flex justify-end"> 
            <Button variant="default">
              <span> View Historical Data </span>
            </Button>
        </div>
      )
    },
  },
]

export default function Dashboard() {
  const { id } = useId();

  const [data, setData] = useState<ParsedToilet[]>([]);
  const [loading, setLoading] = useState(true);
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  )
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})

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
  })

  useEffect(() => {
    if (!id) return;

    async function fetchOccupancy(mallId: number) {
      // setData(parseMallToiletOccupancy(toiletdata))
      // setLoading(false);
      // console.log(data)
      // return;
      try {
        // 1. Fetch all toilets
        const toiletsRes = await getToiletsMallsMallIdToiletsGet({
          path: { mall_id: mallId },
        });

        const toilets = toiletsRes.data?.toilets ?? [];

        // 2. Fetch cubicles for each toilet in parallel
        const cubicleResponses = await Promise.all(
          toilets.map((toilet) =>
            getCubiclesMallsMallIdToiletsToiletIdCubiclesGet({
              path: { mall_id: mallId, toilet_id: toilet.id },
            })
          )
        );

        // 3. Build nested structure
        const nestedToilets: Toilet[] = toilets.map((toilet, index) => {
          const cubicles: CubicleDto[] =
            cubicleResponses[index].data?.cubicles ?? [];

          const occupiedCount = cubicles.filter((c) => c.occupied).length;
          const total = cubicles.length;

          return {
            ...toilet,
            cubicles,
            total_cubicles: total,
            occupied_count: occupiedCount,
            occupancy_percentage: total ? occupiedCount / total : 0,
          };
        });

        // 4. Set state
        setData(parseMallToiletOccupancy({ mall_id: mallId, toilets: nestedToilets }))
      } catch (err) {
        console.error("Failed to fetch mall occuancy", err);
      } finally {
        setLoading(false);
      }
    }

    fetchOccupancy(id);
  }, [id]);

  if (!id) return <div>No ID found. Please sign in again.</div>;
  if (loading) return <div>Loading dashboard…</div>;

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
    <div className="w-10/12">
      <div className="flex items-center py-4">
        <Input
          placeholder="Filter Names..."
          value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
          onChange={(event) =>
            table.getColumn("name")?.setFilterValue(event.target.value)
          }
          className="max-w-sm"
        />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto">
              Columns <ChevronDown />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) =>
                      column.toggleVisibility(!!value)
                    }
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                )
              })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="overflow-hidden rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end space-x-2 py-4">
        <div className="space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
    </div>
  )
}

