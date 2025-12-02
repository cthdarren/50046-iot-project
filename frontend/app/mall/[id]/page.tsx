"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  getToiletsMallsMallIdToiletsGet,
  CubicleDto,
} from "../../services/availability";
import { MallToiletOccupancy, Toilet } from "@/app/models/models";
import { usePolling } from "@/hooks/use-polling";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

export default function Home() {
  const [data, setData] = useState<MallToiletOccupancy>();
  const [loading, setLoading] = useState(true);

  // NEW: Filter and Sort
  const [genderFilter, setGenderFilter] = useState("all");
  const [sortMode, setSortMode] = useState("none"); // "none" | "occ-asc"

  const params = useParams();
  const router = useRouter();

  async function fetchOccupancy() {
    if (params.id === undefined) return;
    const mallId = parseInt(params.id.toString());

    try {
      const toiletsRes = await getToiletsMallsMallIdToiletsGet({
        path: { mall_id: mallId },
      });

      const toilets = toiletsRes.data?.toilets ?? [];

      const cubicleResponses = await Promise.all(
        toilets.map((toilet) =>
          getCubiclesMallsMallIdToiletsToiletIdCubiclesGet({
            path: { mall_id: mallId, toilet_id: toilet.id },
          })
        )
      );

      const nestedToilets: Toilet[] = toilets.map((toilet, index) => {
        const cubicles: CubicleDto[] = cubicleResponses[index].data?.cubicles ?? [];
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

      setData({ mall_id: mallId, toilets: nestedToilets });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  usePolling(fetchOccupancy);

  useEffect(() => {
    if (!params.id) return;
    fetchOccupancy();
  }, [params.id]);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data available.</div>;

  // --------------------------
  //   GROUP BY LEVEL
  // --------------------------
  function groupByLevel(toilets: Toilet[]) {
    const groups: Record<string, Toilet[]> = {};
    toilets.forEach((t) => {
      const level = t.level?.toString() ?? "Unknown";
      if (!groups[level]) groups[level] = [];
      groups[level].push(t);
    });
    return groups;
  }

  // --------------------------
  //   SORTING
  // --------------------------
  function sortToilets(toilets: Toilet[]) {
    const sorted = [...toilets];

    if (sortMode === "occ-asc") {
      sorted.sort((a, b) => a.occupancy_percentage - b.occupancy_percentage);
    }
    // else: default = ID order (API already provides in ID order)

    return sorted;
  }

  // --------------------------
  //   FILTERING
  // --------------------------
  const filteredToilets = data.toilets.filter((t) => {
    if (genderFilter === "all") return true;
    return t.gender.toLowerCase() === genderFilter;
  });

  const grouped = groupByLevel(filteredToilets);

  return (
    <div className="p-4">
      <button
        onClick={() => router.push("/")}
        className="mb-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded"
      >
        ← Back
      </button>

      {/* FILTER + SORT BAR */}
      <div className="flex gap-6 mb-6 items-end">
        {/* GENDER FILTER */}
        <div className="flex flex-col">
          <label className="text-sm font-medium">Gender</label>
          <Select value={genderFilter} onValueChange={setGenderFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="male">Male</SelectItem>
              <SelectItem value="female">Female</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* SORTING */}
        <div className="flex flex-col">
          <label className="text-sm font-medium">Sort by</label>
          <Select value={sortMode} onValueChange={setSortMode}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Sort" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">Default (ID order)</SelectItem>
              <SelectItem value="occ-asc">Occupancy (Low → High)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* COLLAPSIBLE LEVELS */}
      <div className="space-y-6">
        {Object.entries(grouped).map(([level, toilets]) => (
          <Collapsible key={level} className="border rounded-lg p-4">
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="w-full justify-between text-lg font-bold">
                {level}
                <span className="text-sm opacity-60">(expand)</span>
              </Button>
            </CollapsibleTrigger>

            <CollapsibleContent className="mt-4 space-y-4">
              {sortToilets(toilets).map((toilet) => (
                <div key={toilet.id} className="border rounded p-3">
                  <h2 className="font-bold text-lg">
                    {toilet.description} •{" "}
                    <span className="capitalize">{toilet.gender}</span>
                  </h2>

                  <p>
                    Occupancy: {toilet.occupied_count}/{toilet.total_cubicles} (
                    {(toilet.occupancy_percentage * 100).toFixed(1)}%)
                  </p>

                  <div className="mt-3 space-y-1">
                    {toilet.cubicles.map((c) => (
                      <div
                        key={c.id}
                        className={`p-2 rounded text-sm ${
                          c.occupied ? "bg-red-200" : "bg-green-200"
                        }`}
                      >
                        Cubicle {c.id} —{" "}
                        <strong>{c.occupied ? "Occupied" : "Available"}</strong> • Roll:{" "}
                        {c.toilet_roll_percentage}%
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        ))}
      </div>
    </div>
  );
}
