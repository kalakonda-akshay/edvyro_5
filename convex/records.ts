import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Generic insert/sync mutation
export const insertRecord = mutation({
  args: {
    table: v.string(),
    data: v.any(),
  },
  handler: async (ctx, args) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const id = await ctx.db.insert(args.table as any, args.data);
    return id;
  },
});

// Generic batch sync mutation
export const batchSync = mutation({
  args: {
    table: v.string(),
    records: v.array(v.any()),
  },
  handler: async (ctx, args) => {
    const insertedIds = [];
    for (const record of args.records) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const id = await ctx.db.insert(args.table as any, record);
      insertedIds.push(id);
    }
    return insertedIds;
  },
});

// Generic query by table
export const listTable = query({
  args: {
    table: v.string(),
  },
  handler: async (ctx, args) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return await ctx.db.query(args.table as any).collect();
  },
});
