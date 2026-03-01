// Shell hook — will be wired to real KB API in Step 7
export function useKnowledgeBase() {
  return {
    projects: [] as { id: string; name: string }[],
    documents: [] as { id: string; title: string }[],
    loading: false,
  };
}
