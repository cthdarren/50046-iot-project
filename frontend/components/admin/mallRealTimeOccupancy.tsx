import { MallToiletOccupancy, ParsedToilet, Toilet } from "@/app/models/models";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
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
import { ColumnDef, ColumnFiltersState, flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel, getSortedRowModel, SortingState, useReactTable, VisibilityState } from "@tanstack/react-table";
import { Button } from "../ui/button";
import { ArrowUpDown, ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";
import React from "react";
import { useId } from "@/context/IdContext";
import { getToiletsMallsMallIdToiletsGet, getCubiclesMallsMallIdToiletsToiletIdCubiclesGet, CubicleDto } from "@/app/services/availability";
import { usePolling } from "@/hooks/use-polling";
import { useRouter } from "next/navigation";



export default function RealTimeOccupancyTable() {
  const { id } = useId();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ParsedToilet[]>([]);
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  )
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const router = useRouter();



 const columns: ColumnDef<ParsedToilet>[] = [
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
  accessorKey: "hasZeroRoll",
  header: () => <div className="text-right">Status</div>,
  cell: ({ row }) => {
    const isZero = row.getValue("hasZeroRoll") as boolean;

    return (
      <div className="text-right font-medium">
        {isZero ? (
          <span className="text-red-600 font-bold">🔴 Low Toilet Roll</span>
        ) : (
          <span className="text-green-600">🟢 OK</span>
        )}
      </div>
    );
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
            <Button variant="default" onClick={() => {viewHistoricalData(row.original.id.toString())}}>
              <span> View Historical Data </span>
            </Button>
        </div>
      )
    },
  },
]

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

function viewHistoricalData(lol: string){
    console.log(lol)
    router.push(`dashboard/toilet/${lol}`)
}


function parseMallToiletOccupancy(
  mall: MallToiletOccupancy
): ParsedToilet[] {
  return mall.toilets.map((t) => ({
    id: t.id,
    name: t.description,
    level: t.level,
    occupancy: `${t.occupied_count}/${t.total_cubicles}`,
    hasZeroRoll: t.cubicles.some((c) => (c.toilet_roll_percentage ?? 0) < 15),
  }));
}

    async function fetchOccupancy() {
      // setData(parseMallToiletOccupancy(toiletdata))
      // setLoading(false);
      // console.log(data)
      // return;
      if (!id) return;
      const mallId = id;
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

  useEffect(() => {
    fetchOccupancy();
  }, [id]);

  usePolling(fetchOccupancy);
    return(
        <>
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
      <div className="rounded-md border">
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
      </>
    )}
