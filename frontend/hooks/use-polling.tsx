import { useEffect } from "react";

export function usePolling(fetchOccupancy: () => Promise<void>) {
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    // Start polling
    intervalId = setInterval(() => {
      fetchOccupancy();
    }, 3000); // 3 seconds

    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [fetchOccupancy]);
}
