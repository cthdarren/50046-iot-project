"use client";

import { useEffect, useState } from "react";
import { useId } from "@/context/IdContext";
import {
  getCubiclesMallsMallIdToiletsToiletIdCubiclesGet,
  getToiletsMallsMallIdToiletsGet
} from "../services/availability";

export default function Dashboard() {
  const { id } = useId();

  const [toilets, setToilets] = useState<any[]>([]);
  const [cubicles, setCubicles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    async function loadData() {
      if (!id) return;
      try {
        // 1. Fetch all toilets for this mall
        const toiletRes = await getToiletsMallsMallIdToiletsGet({
          path: { mall_id: id }
        });

        const toiletList = toiletRes.data?.toilets ?? [];
        setToilets(toiletList);

        // 2. Fetch cubicles for each toilet in parallel
        const cubiclePromises = toiletList.map((toilet: any) =>
          getCubiclesMallsMallIdToiletsToiletIdCubiclesGet({
            path: {
              mall_id: id,
              toilet_id: toilet.id
            }
          })
        );

        const cubicleResults = await Promise.all(cubiclePromises);

        // 3. Flatten all cubicles from all toilets into one list
        const allCubicles = cubicleResults.flatMap(
          (res) => res.data?.cubicles ?? []
        );

        setCubicles(allCubicles);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [id]);

  if (!id) return <div>No ID found. Please sign in again.</div>;
  if (loading) return <div>Loading dashboard…</div>;

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <div className="p-8">
        <h1 className="text-2xl mb-4">Dashboard</h1>

        <h2 className="text-xl mb-2">Toilets</h2>
        <pre className="bg-white p-4 rounded shadow">
          {JSON.stringify(toilets, null, 2)}
        </pre>

        <h2 className="text-xl mb-2 mt-6">All Cubicles</h2>
        <pre className="bg-white p-4 rounded shadow">
          {JSON.stringify(cubicles, null, 2)}
        </pre>

        {/* Replace these PRE blocks later with shadcn table */}
      </div>
    </div>
  );
}

