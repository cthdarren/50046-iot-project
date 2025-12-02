import { CubicleDto } from "../services/availability";

export type Toilet = {
  id: number;
  level: string;
  gender: string;
  description: string;
  mall_id: number;

  // nested cubicles
  cubicles: CubicleDto[];

  // computed data
  total_cubicles: number;
  occupied_count: number;
  occupancy_percentage: number;
};

export type MallToiletOccupancy = {
  mall_id: number;
  toilets: Toilet[];
};

export type ParsedToilet = {
  name: string;
  level: string;
  occupancy: string;
};
