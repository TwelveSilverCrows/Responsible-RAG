import type { Conversation, Message, Citation } from '@/types/chat';
import { mockSources } from '@/lib/mockData';

// ── Helper ──────────────────────────────────────────────────
const now = new Date();
const today = (h: number, m: number) => {
  const d = new Date(now);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
};
const yesterday = (h: number, m: number) => {
  const d = new Date(now);
  d.setDate(d.getDate() - 1);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
};
const daysAgo = (days: number, h: number, m: number) => {
  const d = new Date(now);
  d.setDate(d.getDate() - days);
  d.setHours(h, m, 0, 0);
  return d.toISOString();
};

// ── Conversations ───────────────────────────────────────────
export const mockConversations: Conversation[] = [
  {
    id: 'conv-001',
    title: 'Responsible AI best practices',
    lastMessage: 'Transparency and fairness are key pillars of responsible AI.',
    lastMessageAt: today(10, 32),
    createdAt: today(10, 15),
    messageCount: 4,
  },
  {
    id: 'conv-002',
    title: 'RAG system architecture',
    lastMessage: 'RAG combines retrieval with generation for grounded responses.',
    lastMessageAt: today(9, 5),
    createdAt: today(9, 0),
    messageCount: 4,
  },
  {
    id: 'conv-003',
    title: 'Privacy-first design principles',
    lastMessage: 'Privacy-by-design ensures data protection from the start.',
    lastMessageAt: yesterday(16, 45),
    createdAt: yesterday(16, 30),
    messageCount: 4,
  },
  {
    id: 'conv-004',
    title: 'Bias detection in language models',
    lastMessage:
      'Novel methodologies for detecting bias in LLMs are emerging rapidly.',
    lastMessageAt: yesterday(11, 20),
    createdAt: yesterday(11, 0),
    messageCount: 4,
  },
  {
    id: 'conv-005',
    title: 'AI governance and compliance',
    lastMessage: 'Governance frameworks help ensure AI systems are accountable.',
    lastMessageAt: daysAgo(3, 14, 10),
    createdAt: daysAgo(3, 14, 0),
    messageCount: 4,
  },
  {
    id: 'conv-006',
    title: 'Understanding transformers',
    lastMessage: 'Self-attention is the core mechanism behind transformer models.',
    lastMessageAt: daysAgo(5, 9, 30),
    createdAt: daysAgo(5, 9, 0),
    messageCount: 4,
  },
];

// ── Citations ───────────────────────────────────────────────
export const mockCitations: Citation[] = [
  {
    id: 'cit-001',
    sourceId: 'src-001',
    source: mockSources[0],
    excerpt:
      'Responsible AI practices must embed fairness, transparency, and accountability into every stage of the system lifecycle, from data collection to deployment and monitoring.',
    number: 1,
  },
  {
    id: 'cit-002',
    sourceId: 'src-002',
    source: mockSources[1],
    excerpt:
      'RAG architectures combine information retrieval with language generation, allowing models to ground their responses in verified source material rather than relying solely on parametric knowledge.',
    number: 2,
  },
  {
    id: 'cit-003',
    sourceId: 'src-003',
    source: mockSources[2],
    excerpt:
      'Privacy-first design principles require that data minimization, purpose limitation, and user consent are embedded as foundational requirements, not afterthoughts.',
    number: 3,
  },
  {
    id: 'cit-004',
    sourceId: 'src-007',
    source: mockSources[6],
    excerpt:
      'We propose a multi-dimensional bias detection framework that measures representation, stereotyping, and performative gaps across demographic groups in language model outputs.',
    number: 4,
  },
  {
    id: 'cit-005',
    sourceId: 'src-004',
    source: mockSources[3],
    excerpt:
      'All AI systems processing personal or sensitive data must undergo an ethics review and be registered in the organizational AI inventory before deployment.',
    number: 5,
  },
  {
    id: 'cit-006',
    sourceId: 'src-008',
    source: mockSources[7],
    excerpt:
      'The self-attention mechanism allows each token to attend to every other token in the sequence, computing weighted sums that capture contextual relationships.',
    number: 6,
  },
  {
    id: 'cit-007',
    sourceId: 'src-001',
    source: mockSources[0],
    excerpt:
      'Transparency requirements include documenting model capabilities, limitations, and potential risks in accessible language for all stakeholders.',
    number: 7,
  },
  {
    id: 'cit-008',
    sourceId: 'src-002',
    source: mockSources[1],
    excerpt:
      'Enterprise RAG deployments show 40% reduction in hallucination rates when retrieval relevance thresholds are properly calibrated.',
    number: 8,
  },
];

// ── Messages ────────────────────────────────────────────────
export const mockMessages: Message[] = [
  // Conv 1 — Responsible AI best practices
  {
    id: 'msg-001',
    conversationId: 'conv-001',
    role: 'user',
    content: 'What are the key principles of responsible AI?',
    citations: [],
    createdAt: today(10, 15),
  },
  {
    id: 'msg-002',
    conversationId: 'conv-001',
    role: 'assistant',
    content:
      'The key principles of responsible AI include [1]:\n\n1. **Fairness** — AI systems should treat all individuals equitably, avoiding discrimination based on protected characteristics.\n2. **Transparency** — Organizations must be open about how AI systems make decisions, what data they use, and what their limitations are [7].\n3. **Accountability** — Clear lines of responsibility must exist for AI system outcomes.\n4. **Privacy** — Personal data should be protected and used only with informed consent.\n5. **Safety** — AI systems should be robust and operate reliably within their intended parameters.\n\nThese principles should be embedded throughout the AI lifecycle, from data collection to deployment and monitoring [1].',
    citations: [mockCitations[0], mockCitations[6]],
    createdAt: today(10, 16),
  },
  {
    id: 'msg-003',
    conversationId: 'conv-001',
    role: 'user',
    content: 'How do organizations implement transparency in practice?',
    citations: [],
    createdAt: today(10, 25),
  },
  {
    id: 'msg-004',
    conversationId: 'conv-001',
    role: 'assistant',
    content:
      'Organizations implement transparency through several mechanisms:\n\n- **Model documentation** — Publishing detailed descriptions of model capabilities, limitations, and potential risks [7]\n- **Decision logs** — Maintaining records of when and how AI systems make consequential decisions\n- **Audit trails** — Creating traceable paths from data inputs to model outputs\n- **Stakeholder communication** — Providing clear, accessible explanations to affected individuals\n\nTransparency and fairness are key pillars of responsible AI. Without transparency, it becomes impossible to verify that AI systems are operating as intended or to identify when they produce harmful outcomes [1].',
    citations: [mockCitations[6], mockCitations[0]],
    createdAt: today(10, 32),
  },

  // Conv 2 — RAG system architecture
  {
    id: 'msg-005',
    conversationId: 'conv-002',
    role: 'user',
    content: 'How does RAG work?',
    citations: [],
    createdAt: today(9, 0),
  },
  {
    id: 'msg-006',
    conversationId: 'conv-002',
    role: 'assistant',
    content:
      'Retrieval-Augmented Generation (RAG) works by combining two key components [2]:\n\n1. **Retrieval** — When a user asks a question, the system first searches a knowledge base for relevant documents or passages using semantic similarity search.\n2. **Generation** — The retrieved context is then passed to a language model along with the user query, allowing the model to generate a grounded, factual response.\n\nThis approach significantly reduces hallucination because the model can reference actual source material rather than relying solely on its training data [2]. Enterprise deployments have shown up to 40% reduction in hallucination rates when retrieval is properly calibrated [8].',
    citations: [mockCitations[1], mockCitations[7]],
    createdAt: today(9, 2),
  },
  {
    id: 'msg-007',
    conversationId: 'conv-002',
    role: 'user',
    content: 'What are the main challenges with RAG systems?',
    citations: [],
    createdAt: today(9, 3),
  },
  {
    id: 'msg-008',
    conversationId: 'conv-002',
    role: 'assistant',
    content:
      'RAG combines retrieval with generation for grounded responses. The main challenges include:\n\n- **Retrieval quality** — If the retrieval component returns irrelevant or low-quality passages, the generated response will be poor\n- **Context window limits** — There is a maximum amount of retrieved text that can fit into the model context\n- **Latency** — The retrieval step adds overhead compared to pure generation\n- **Chunking strategy** — How documents are split into passages significantly affects retrieval quality\n- **Freshness** — Keeping the knowledge base up to date with new information\n\nCalibrating retrieval relevance thresholds is critical — too strict and you miss useful context, too loose and you introduce noise [8].',
    citations: [mockCitations[7]],
    createdAt: today(9, 5),
  },

  // Conv 3 — Privacy-first design
  {
    id: 'msg-009',
    conversationId: 'conv-003',
    role: 'user',
    content: 'What does privacy-by-design mean?',
    citations: [],
    createdAt: yesterday(16, 30),
  },
  {
    id: 'msg-010',
    conversationId: 'conv-003',
    role: 'assistant',
    content:
      'Privacy-by-design is an approach where privacy and data protection are embedded into the design and architecture of IT systems from the very beginning [3]. The seven foundational principles are:\n\n1. **Proactive not reactive** — Anticipate and prevent privacy issues before they occur\n2. **Privacy as default** — Personal data is automatically protected in any system\n3. **Privacy embedded into design** — Privacy is a core design consideration, not an add-on\n4. **Full functionality** — Privacy does not reduce functionality\n5. **End-to-end security** — Full lifecycle protection of personal data\n6. **Visibility and transparency** — All stakeholders can verify privacy practices\n7. **Respect for user privacy** — Individual interests are prioritized\n\nPrivacy-first design ensures data protection from the start [3].',
    citations: [mockCitations[2]],
    createdAt: yesterday(16, 35),
  },
  {
    id: 'msg-011',
    conversationId: 'conv-003',
    role: 'user',
    content: 'How does this apply to AI systems specifically?',
    citations: [],
    createdAt: yesterday(16, 40),
  },
  {
    id: 'msg-012',
    conversationId: 'conv-003',
    role: 'assistant',
    content:
      'For AI systems, privacy-by-design requires:\n\n- **Data minimization** — Collect only the data strictly necessary for the AI system to function [3]\n- **Purpose limitation** — Use personal data only for the stated purpose\n- **Federated learning** — Train models on-device without centralizing data\n- **Differential privacy** — Add statistical noise to protect individual records\n- **Consent mechanisms** — Give users meaningful control over their data\n\nThese principles are especially important in RAG systems where user queries and retrieved documents may contain sensitive information [3].',
    citations: [mockCitations[2]],
    createdAt: yesterday(16, 45),
  },

  // Conv 4 — Bias detection
  {
    id: 'msg-013',
    conversationId: 'conv-004',
    role: 'user',
    content: 'How do we detect bias in language models?',
    citations: [],
    createdAt: yesterday(11, 0),
  },
  {
    id: 'msg-014',
    conversationId: 'conv-004',
    role: 'assistant',
    content:
      'Bias detection in language models involves several methodologies [4]:\n\n- **Representation analysis** — Measuring how different demographic groups are represented in training data and model outputs\n- **Stereotyping assessment** — Evaluating whether model outputs reinforce harmful stereotypes\n- **Performative gap analysis** — Comparing model performance across demographic groups\n- **Counterfactual testing** — Substituting identity terms to measure differential treatment\n\nNovel methodologies for detecting bias in LLMs are emerging rapidly. A multi-dimensional framework that measures representation, stereotyping, and performative gaps simultaneously provides the most comprehensive assessment [4].',
    citations: [mockCitations[3]],
    createdAt: yesterday(11, 10),
  },
  {
    id: 'msg-015',
    conversationId: 'conv-004',
    role: 'user',
    content: 'What mitigation strategies exist?',
    citations: [],
    createdAt: yesterday(11, 15),
  },
  {
    id: 'msg-016',
    conversationId: 'conv-004',
    role: 'assistant',
    content:
      'Common bias mitigation strategies include:\n\n- **Data curation** — Carefully balancing training datasets across demographics\n- **Debiasing algorithms** — Applying mathematical techniques to reduce learned biases\n- **Output filtering** — Screening generated text for biased content\n- **Human-in-the-loop** — Incorporating human review for high-stakes decisions\n- **Regular auditing** — Conducting periodic bias assessments on deployed models\n\nThe key insight is that no single technique is sufficient — effective mitigation requires a combination of approaches applied throughout the model lifecycle [4].',
    citations: [mockCitations[3]],
    createdAt: yesterday(11, 20),
  },

  // Conv 5 — AI governance
  {
    id: 'msg-017',
    conversationId: 'conv-005',
    role: 'user',
    content: 'What should an AI governance framework include?',
    citations: [],
    createdAt: daysAgo(3, 14, 0),
  },
  {
    id: 'msg-018',
    conversationId: 'conv-005',
    role: 'assistant',
    content:
      'An effective AI governance framework should include [5]:\n\n- **Ethics review board** — A cross-functional team that reviews AI projects for ethical concerns\n- **AI inventory** — A registry of all AI systems, their purposes, and risk classifications\n- **Impact assessments** — Mandatory assessments before deploying high-risk AI systems\n- **Compliance monitoring** — Ongoing verification that AI systems meet regulatory requirements\n- **Incident response** — Procedures for handling AI failures or harmful outcomes\n\nAll AI systems processing personal or sensitive data must undergo an ethics review and be registered in the organizational AI inventory before deployment [5].',
    citations: [mockCitations[4]],
    createdAt: daysAgo(3, 14, 5),
  },
  {
    id: 'msg-019',
    conversationId: 'conv-005',
    role: 'user',
    content: 'How do you balance innovation with compliance?',
    citations: [],
    createdAt: daysAgo(3, 14, 5),
  },
  {
    id: 'msg-020',
    conversationId: 'conv-005',
    role: 'assistant',
    content:
      'Balancing innovation with compliance requires [5]:\n\n- **Sandboxed environments** — Safe spaces for experimentation without production risk\n- **Tiered risk frameworks** — More governance for higher-risk applications, less for experimental ones\n- **Iterative review** — Lightweight check-ins during development rather than heavy gates\n- **Cross-functional collaboration** — Legal, ethics, and engineering teams working together from the start\n\nGovernance frameworks help ensure AI systems are accountable while still allowing teams to iterate and innovate [5].',
    citations: [mockCitations[4]],
    createdAt: daysAgo(3, 14, 10),
  },

  // Conv 6 — Understanding transformers
  {
    id: 'msg-021',
    conversationId: 'conv-006',
    role: 'user',
    content: 'How does the self-attention mechanism work?',
    citations: [],
    createdAt: daysAgo(5, 9, 0),
  },
  {
    id: 'msg-022',
    conversationId: 'conv-006',
    role: 'assistant',
    content:
      'The self-attention mechanism works by computing a weighted sum of all values in a sequence, where the weights are determined by the compatibility between queries and keys [6]:\n\n1. **Query, Key, Value** — Each input token is transformed into three vectors\n2. **Attention scores** — Dot products between queries and keys determine relevance\n3. **Softmax** — Scores are normalized to sum to 1\n4. **Weighted sum** — Values are combined according to the attention weights\n\nSelf-attention is the core mechanism behind transformer models. It allows each token to attend to every other token, capturing both local and long-range dependencies [6].\n\n```python\n# Simplified self-attention\nattention_scores = queries @ keys.T / sqrt(d_k)\nattention_weights = softmax(attention_scores)\noutput = attention_weights @ values\n```',
    citations: [mockCitations[5]],
    createdAt: daysAgo(5, 9, 10),
  },
  {
    id: 'msg-023',
    conversationId: 'conv-006',
    role: 'user',
    content: 'What are multi-head attention and positional encoding?',
    citations: [],
    createdAt: daysAgo(5, 9, 15),
  },
  {
    id: 'msg-024',
    conversationId: 'conv-006',
    role: 'assistant',
    content:
      'Two critical extensions to basic self-attention:\n\n**Multi-head attention** runs multiple attention operations in parallel, each with different learned projections. This allows the model to attend to different types of relationships simultaneously:\n\n- One head might focus on syntactic relationships\n- Another on semantic similarity\n- Another on positional proximity\n\n**Positional encoding** injects sequence order information since self-attention is permutation-invariant by default. The original Transformer uses sinusoidal encodings:\n\n```\nPE(pos, 2i)   = sin(pos / 10000^(2i/d))\nPE(pos, 2i+1) = cos(pos / 10000^(2i/d))\n```\n\nTogether, these mechanisms give transformers their remarkable ability to model complex sequential relationships [6].',
    citations: [mockCitations[5]],
    createdAt: daysAgo(5, 9, 30),
  },
];

/**
 * Simulated streaming responses — used when the user sends a new message.
 * Each entry is a complete assistant response that will "stream in".
 */
export const streamingResponses: string[] = [
  'That\'s a great question. Responsible AI is built on the foundation of **fairness**, **transparency**, and **accountability** [1].\n\nIn practice, this means:\n\n- Ensuring training data represents diverse populations\n- Documenting model capabilities and limitations clearly\n- Establishing clear accountability structures\n- Protecting user privacy at every stage\n\nThese principles are not just ethical guidelines — they are practical requirements for building AI systems that people can trust [1].',

  'RAG systems address a fundamental limitation of language models: their knowledge is frozen at training time [2].\n\nBy combining retrieval with generation, RAG allows models to:\n\n1. Access up-to-date information\n2. Cite specific sources for verification\n3. Reduce hallucination significantly\n4. Adapt to new domains without retraining\n\nThe key insight is that separation of knowledge storage (in the retrieval index) from reasoning (in the language model) creates a more maintainable and trustworthy system [2].',

  'Privacy considerations in AI go beyond simple data protection [3]:\n\n- **Data minimization** — Only collect what you truly need\n- **Purpose binding** — Use data only for its stated purpose\n- **Transparency** — Let users know how their data is used\n- **User control** — Give users meaningful choices about their data\n\nPrivacy-by-design is not optional — it\'s a fundamental requirement for trustworthy AI systems [3].',
];
