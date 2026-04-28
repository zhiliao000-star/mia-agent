import { v } from "convex/values";
import { internalMutation, internalQuery, query } from "./_generated/server";

export const createHold = internalMutation({
  args: {
    title: v.string(),
    day: v.string(),
    time: v.string(),
    sourceMessageHandle: v.string(),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    const id = await ctx.db.insert("calendarHolds", {
      title: args.title,
      day: args.day,
      time: args.time,
      sourceMessageHandle: args.sourceMessageHandle,
      status: "tentative",
      createdAt: now,
      updatedAt: now,
    });
    return { id };
  },
});

export const listForDay = internalQuery({
  args: { day: v.string() },
  handler: async (ctx, args) => {
    const holds = await ctx.db
      .query("calendarHolds")
      .withIndex("by_day", (q) => q.eq("day", args.day))
      .collect();
    return { holds: holds.filter((hold) => hold.status !== "cancelled") };
  },
});

export const recent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("calendarHolds")
      .withIndex("by_created_at")
      .order("desc")
      .take(args.limit ?? 10);
  },
});
