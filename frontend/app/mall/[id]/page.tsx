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

export default function Home() {
  const [data, setData] = useState<MallToiletOccupancy>();
  const [loading, setLoading] = useState(true);

  const params = useParams();
  const router = useRouter();

  // // --- mock data ---
  // const toiletdata: MallToiletOccupancy = {
  //   mall_id: 1,
  //   toilets: [
  //     {
  //       id: 101,
  //       level: "B1",
  //       gender: "Male",
  //       description: "Near Food Court",
  //       mall_id: 1,
  //       cubicles: [
  //         { id: 1, toilet_id: 101, occupied: true, toilet_roll_percentage: 45 },
  //         { id: 2, toilet_id: 101, occupied: false, toilet_roll_percentage: 80 },
  //         { id: 3, toilet_id: 101, occupied: true, toilet_roll_percentage: 60 },
  //       ],
  //       total_cubicles: 3,
  //       occupied_count: 2,
  //       occupancy_percentage: 66.7,
  //     },
  //     {
  //       id: 102,
  //       level: "L1",
  //       gender: "Female",
  //       description: "Next to Zara",
  //       mall_id: 1,
  //       cubicles: [
  //         { id: 4, toilet_id: 102, occupied: false, toilet_roll_percentage: 90 },
  //         { id: 5, toilet_id: 102, occupied: false, toilet_roll_percentage: 70 },
  //         { id: 6, toilet_id: 102, occupied: true, toilet_roll_percentage: 50 },
  //         { id: 7, toilet_id: 102, occupied: false, toilet_roll_percentage: 30 },
  //       ],
  //       total_cubicles: 4,
  //       occupied_count: 1,
  //       occupancy_percentage: 25,
  //     },
  //   ],
  // };

  useEffect(() => {
    if (!params.id) return;

    async function fetchOccupancy(mallId: number) {
      // // mock data for now
      // setData(toiletdata);
      // setLoading(false);
      // console.log(data);
      // console.log(mallId);
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
        setData(({ mall_id: mallId, toilets: nestedToilets }))
      } catch (err) {
        console.error("Failed to fetch mall occuancy", err);
      } finally {
        setLoading(false);
      }
      // --- end preserved block ---
    }

    fetchOccupancy(parseInt(params.id.toString()));
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
              Toilet {toilet.id} — {toilet.gender} ({toilet.level})
            </h2>
            <p className="text-sm text-gray-600 mb-2">{toilet.description}</p>

            <p>
              <strong>Occupied:</strong> {toilet.occupied_count}/{toilet.total_cubicles} (
              {toilet.occupancy_percentage}%)
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
