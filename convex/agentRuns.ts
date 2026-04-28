import { v } from "convex/values";
import { internalMutation, query } from "./_generated/server";

export const start = internalMutation({
  args: { runId: v.string(), messageHandle: v.string() },
  handler: async (ctx, args) => {
    await ctx.db.insert("agentRuns", {
      runId: args.runId,
      messageHandle: args.messageHandle,
      activeAgent: "parent_router",
      status: "running",
      startedAt: Date.now(),
    });
    return { ok: true };
  },
});

export const complete = internalMutation({
  args: { runId: v.string(), activeAgent: v.string() },
  handler: async (ctx, args) => {
    const run = await ctx.db
      .query("agentRuns")
      .withIndex("by_run_id", (q) => q.eq("runId", args.runId))
      .unique();
    if (run) {
      await ctx.db.patch(run._id, {
        activeAgent: args.activeAgent,
        status: "completed",
        completedAt: Date.now(),
      });
    }
    return { ok: true };
  },
});

export const fail = internalMutation({
  args: { runId: v.string(), error: v.string() },
  handler: async (ctx, args) => {
    const run = await ctx.db
      .query("agentRuns")
      .withIndex("by_run_id", (q) => q.eq("runId", args.runId))
      .unique();
    if (run) {
      await ctx.db.patch(run._id, {
        status: "failed",
        completedAt: Date.now(),
        error: args.error,
      });
    }
    return { ok: true };
  },
});

export const recent = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agentRuns")
      .withIndex("by_started_at")
      .order("desc")
      .take(args.limit ?? 10);
  },
});

export const active = query({
  args: {},
  handler: async (ctx) => {
    const running = await ctx.db
      .query("agentRuns")
      .withIndex("by_started_at")
      .order("desc")
      .filter((q) => q.eq(q.field("status"), "running"))
      .first();
    return running?.activeAgent ?? null;
  },
});
