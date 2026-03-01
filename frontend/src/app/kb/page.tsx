"use client";

import { BookOpen } from "lucide-react";

export default function KnowledgeBasePage() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center py-20">
        <BookOpen className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-900">Knowledge Base</h2>
        <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
          Upload PDFs and saved papers for semantic search. This feature will be
          available after the Pinecone integration is complete (Step 7).
        </p>
      </div>
    </div>
  );
}
