"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  getMallsMallsGet,
  getToiletsMallsMallIdToiletsGet,
} from "../../services/availability";
import type { CubicleDto } from "../../services/availability";
import { useParams } from "next/navigation";
import { MallToiletOccupancy, Toilet } from "@/app/models/models";
import { usePolling } from "@/hooks/use-polling";

export default function Home() {
  const [data, setData] = useState<MallToiletOccupancy>();
  const [loading, setLoading] = useState(true);

  const params = useParams();
  const router = useRouter();

async function fetchOccupancy() {
  if (params.id === undefined) return;
  const mallId = parseInt(params.id.toString())
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
    setData(({ mall_id: mallId, toilets: nestedToilets }))
  } catch (err) {
    console.error("Failed to fetch mall occuancy", err);
  } finally {
    setLoading(false);
  }
  // --- end preserved block ---
}

  usePolling(fetchOccupancy)

  useEffect(() => {
    if (!params.id) return;
    fetchOccupancy();
  }, [params.id]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!data) {
    return <div>No data available.</div>;
  }


  return (

    <div className="p-4">
     <button
            onClick={() => router.push("/")}
            className="mb-4 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded"
          >
            ← Back
          </button>
      <div className="space-y-4">
        {data.toilets.map((toilet) => (
          <div key={toilet.id} className="border rounded p-3">
            <h2 className="font-bold text-lg">
              {`${toilet.description} `} - <span className="capitalize">{toilet.gender}</span>
            </h2>

            <p>
              <span>Occupancy:</span> {toilet.occupied_count}/{toilet.total_cubicles} (
              {toilet.occupancy_percentage*100}%)
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
                  <strong>{c.occupied ? "Occupied" : "Available"}</strong> | Roll:{" "}
                  {c.toilet_roll_percentage}%
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
