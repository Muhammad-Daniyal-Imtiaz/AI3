import { LlamaCloudIndex } from 'llama-index-indices-managed-llama-cloud';

export async function POST(request) {
  try {
    const { message } = await request.json();

    const index = new LlamaCloudIndex({
      name: "gentle-impala-2025-05-01",
      projectName: "Default",
      organizationId: "37173c96-dff2-47fc-9f72-854c3d98cf31",
      apiKey: process.env.LLAMA_CLOUD_API_KEY
    });

    // Get relevant documents
    const retriever = index.asRetriever({ similarityTopK: 3 });
    const nodes = await retriever.retrieve(message);
    
    // Format sources
    const sources = nodes.map(node => ({
      content: node.node.getContent(),
      score: parseFloat(node.score)
    }));
    
    // Get response from query engine
    const response = await index.asQueryEngine().query(message);
    
    return Response.json({
      response: response.toString(),
      sources
    });
  } catch (error) {
    console.error('Error:', error);
    return Response.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}