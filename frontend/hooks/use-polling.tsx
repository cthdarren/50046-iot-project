import { useEffect } from "react";

export function usePolling(fetchOccupancy: () => Promise<void>) {
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    // Start polling
    intervalId = setInterval(() => {
      fetchOccupancy();
    }, 1000); // 1 second

    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [fetchOccupancy]);
}
