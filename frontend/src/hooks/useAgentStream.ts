// Shell hook — will be wired to real SSE endpoint in Step 6
export function useAgentStream() {
  return {
    steps: [] as { id: string; agent: string; message: string }[],
    isStreaming: false,
  };
}
