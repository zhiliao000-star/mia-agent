import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

crons.hourly(
  "Mia Memory Court NY 3AM guard",
  { minuteUTC: 0 },
  internal.memoryCourt.maybeRunNightlyCourt,
);

export default crons;
