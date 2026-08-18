```
ai-coding-agent/
│
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── workflows/
│   │   ├── backend-ci.yml
│   │   ├── frontend-ci.yml
│   │   ├── docker.yml
│   │   ├── security.yml
│   │   └── release.yml
│   └── CODEOWNERS
│
├── docs/
│   ├── architecture/
│   │   ├── HLD.md
│   │   ├── LLD.md
│   │   ├── system-design.md
│   │   ├── sequence-diagrams/
│   │   ├── deployment-diagrams/
│   │   └── er-diagrams/
│   │
│   ├── api/
│   ├── security/
│   ├── testing/
│   ├── monitoring/
│   ├── setup/
│   ├── development/
│   ├── decisions/
│   ├── research/
│   └── images/
│
├── backend/
│
│   ├── app/
│   │
│   │── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   ├── constants.py
│   │   ├── exceptions.py
│   │   ├── middleware.py
│   │   ├── dependencies.py
│   │   └── lifespan.py
│   │
│   │── api/
│   │   ├── v1/
│   │   │
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── repositories.py
│   │   ├── projects.py
│   │   ├── chat.py
│   │   ├── indexing.py
│   │   ├── retrieval.py
│   │   ├── agents.py
│   │   ├── github.py
│   │   ├── monitoring.py
│   │   └── admin.py
│   │
│   ├── database/
│   │   ├── session.py
│   │   ├── base.py
│   │   ├── models/
│   │   ├── repositories/
│   │   └── migrations/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── auth/
│   │   ├── repository/
│   │   ├── indexing/
│   │   ├── retrieval/
│   │   ├── embeddings/
│   │   ├── github/
│   │   ├── workspace/
│   │   ├── chat/
│   │   ├── diff/
│   │   ├── documentation/
│   │   ├── review/
│   │   └── analytics/
│   │
│   ├── ai/
│   │   ├── llm/
│   │   │   ├── provider.py
│   │   │   ├── litellm.py
│   │   │   └── prompts/
│   │   │
│   │   ├── agents/
│   │   │   ├── planner.py
│   │   │   ├── coder.py
│   │   │   ├── reviewer.py
│   │   │   ├── critic.py
│   │   │   ├── retriever.py
│   │   │   ├── summarizer.py
│   │   │   └── executor.py
│   │   │
│   │   ├── workflows/
│   │   ├── memory/
│   │   ├── evaluation/
│   │   └── guardrails/
│   │
│   │ 
│   ├── indexing/
│   │   │
│   │   ├── importers/
│   │   │   ├── github_importer.py
│   │   │   ├── zip_importer.py
│   │   │   └── local_importer.py
│   │   │
│   │   ├── scanner/
│   │   │   ├── file_scanner.py
│   │   │   ├── language_detector.py
│   │   │   └── ignore_rules.py
│   │   │
│   │   ├── parser/
│   │   │   ├── tree_sitter_parser.py
│   │   │   ├── metadata_extractor.py
│   │   │   └── ast_utils.py
│   │   │
│   │   ├── chunking/
│   │   │   ├── chunker.py
│   │   │   ├── code_chunker.py
│   │   │   └── markdown_chunker.py
│   │   │
│   │   ├── embeddings/
│   │   │   ├── embedding_service.py
│   │   │   └── models.py
│   │   │
│   │   ├── vectorstore/
│   │   │   ├── qdrant_service.py
│   │   │   └── collections.py
│   │   │
│   │   ├── bm25/
│   │   │   └── bm25_service.py
│   │   │
│   │   └── pipeline.py
│   │
│   ├── tools/
│   │   ├── filesystem/
│   │   ├── shell/
│   │   ├── git/
│   │   ├── python/
│   │   ├── search/
│   │   └── documentation/
│   │
│   ├── workers/
│   │
│   ├── websocket/
│   │
│   ├── telemetry/
│   │
│   ├── utils/
│   │
│   ├── main.py
│   └── __init__.py
│
├── frontend/
│
│   ├── src/
│   │
│   ├── assets/
│   │
│   ├── components/
│   │   ├── common/
│   │   ├── chat/
│   │   ├── editor/
│   │   ├── repository/
│   │   ├── diff/
│   │   ├── dashboard/
│   │   └── ui/
│   │
│   ├── pages/
│   │
│   ├── hooks/
│   │
│   ├── context/
│   │
│   ├── services/
│   │
│   ├── api/
│   │
│   ├── store/
│   │
│   ├── routes/
│   │
│   ├── types/
│   │
│   ├── styles/
│   │
│   ├── utils/
│   │
│   └── App.tsx
│
├── shared/
│   ├── prompts/
│   ├── constants/
│   ├── schemas/
│   └── types/
│
├── scripts/
│   ├── setup.sh
│   ├── dev.sh
│   ├── seed.py
│   ├── backup.py
│   └── benchmark.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   ├── e2e/
│   ├── fixtures/
│   └── mocks/
│
├── infrastructure/
│   ├── docker/
│   │   ├── backend.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── nginx.conf
│   │
│   ├── compose/
│   │   ├── docker-compose.dev.yml
│   │   └── docker-compose.prod.yml
│   │
│   ├── prometheus/
│   ├── grafana/
│   ├── redis/
│   └── postgres/
│
├── deployments/
│   ├── kubernetes/
│   ├── terraform/
│   └── helm/
│
├── datasets/
│
├── experiments/
│
├── notebooks/
│
├── benchmarks/
│
├── examples/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── package.json
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
└── SECURITY.md
```