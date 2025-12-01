"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { ChevronsUpDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { getMallsMallsGet } from "./services/availability";
import type { GetMallsMallsGetData, MallDto } from "./services/availability";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const [malls, setMalls] = useState<MallDto[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [open, setOpen] = useState(false);
  const [selectedMallId, setSelectedMallId] = useState<number | null>(null);

  useEffect(() => {
    const fetchMalls = async () => {
      try {
        setIsLoading(true);
        // ASSUMPTION: getMallsMallsGet() returns Promise<MallDto[]>
        const mallsRes = await getMallsMallsGet();
        // const data: MallDto[] = mallsRes.data?? [];
        const data:MallDto[] = [
          {
            "id": 0,
            "name": "Mall1",
            "toilets": []
          },
          {
            "id": 1,
            "name": "CCP",
            "toilets": []
          }
        ]
        setMalls(data);
      } catch (err) {
        console.error("Failed to load malls", err);
      } finally {
        console.log("fetched malls")
        setIsLoading(false);
      }
    };

    fetchMalls();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedMallId === null) {
      alert("Please select a mall first");
      return;
    }

    // TODO: navigate to your mall detail page
    // e.g. router.push(`/mall/${selectedMallId}`);
    router.push(`/mall/${selectedMallId}`);
    console.log("Selected mall ID:", selectedMallId);
  };

  const selectedMall = selectedMallId !== null
    ? malls.find((m) => m.id === selectedMallId)
    : undefined;

  return (

    <div className="flex w-full h-screen justify-center items-center">
      <div className="flex flex-col">
        <h1 className="text-xl mb-4">Select a Mall</h1>

        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-72 justify-between"
                disabled={isLoading}
              >
                {isLoading
                  ? "Loading malls..."
                  : (selectedMall !== null && selectedMall !== undefined)
                  ? selectedMall.name
                  : "Search and select a mall"}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-0">
              <Command>
                <CommandInput placeholder="Search mall name..." />
                <CommandList>
                  <CommandEmpty>No mall found.</CommandEmpty>
                  <CommandGroup>
                    {malls.map((mall) => (
                      <CommandItem
                        // value is used for filtering by CommandInput
                        key={mall.id}
                        value={`${mall.id}-${mall.name}`}
                        onSelect={(currentValue) => {
                          const idPart = currentValue.split("-")[0];
                          const parsedId = Number(idPart);
                          if (!Number.isNaN(parsedId)) {
                            setSelectedMallId(parsedId);
                          }
                          setOpen(false);
                        }}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            mall.id === selectedMallId
                              ? "opacity-100"
                              : "opacity-0"
                          )}
                        />
                        {mall.name}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          <Button type="submit" className="w-72">
            Continue
          </Button>
        </form>
      </div>
    </div>
  );
}

