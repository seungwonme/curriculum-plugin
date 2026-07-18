# Non-developer vibe-coding glossary

Use this `curriculum-authoring` reference when creating or improving IT/software terminology material for non-developers, especially for AI-assisted development, Cursor, Claude Code, Lovable, Next.js/Supabase/Vercel, or "바이브 코딩" education.

## Positioning

Do not frame it as a developer dictionary. Frame it as a translation layer that helps non-developers:

1. understand what the AI coding tool is saying,
2. give more precise instructions,
3. inspect whether the result is actually safe and working.

Core promise:

> 좋은 비개발자 바이브 코더는 모든 코드를 외우는 사람이 아니라, 좋은 질문·완료 기준·검수 기준을 가진 사람이다.

## Source synthesis pattern

When multiple references are provided, synthesize by role:

- Introductory article: capture pain points and learner language. Typical pain points: terminal/CLI confusion, npm/pip "where do I type this?", GitHub/version anxiety, token/context limits, AI changing files unexpectedly.
- Existing Notion/lecture page: capture course structure, teaching order, and stack choices. For vibe-coding basics, useful spine: AI 시대 학습법 -> 웹 개발 큰 그림 -> frontend/backend/DB/API -> tools -> debugging -> glossary.
- Deep PDF/book: use it to expand durable CS background terms, but keep them in a "deeper background" section rather than forcing all into the first lesson.

## Recommended structure

1. Why this glossary exists
2. How to use it: don't memorize; locate the term, ask AI to explain it in the current project, then verify
3. First 25 terms for the first 30 minutes
4. Vibe-coding work terms: prompt, context, requirement, acceptance criteria, agent, token, rules file
5. App map: frontend, backend, client, server, database, API, architecture
6. UI/UX terms: UI, UX, page, component, state, form, validation, empty/loading/error states, responsive
7. Language/tool terms: programming language, runtime, framework, library, SDK, module, package, dependency, package manager, IDE, terminal, CLI, GUI, Markdown, JSON, CSV
8. Git/collaboration: Git, GitHub, repo, branch, commit, push, pull, PR, merge, conflict
9. API/network: HTTP/HTTPS, request/response, endpoint, methods, status codes, REST, OpenAPI, CORS, webhook, sync/async, polling/event
10. Data/auth/security: DBMS, SQL/NoSQL, table/column/row/schema/relation/CRUD/query/index/migration/transaction/cache, authn/authz, session/cookie/token/OAuth/role/RLS/secret/API key/rate limit
11. Debugging/testing: bug, error, stack trace, console, log, debug, console.log, lint, type error, test, regression, mock data, rollback, diff
12. Deploy/ops/cloud: local/dev/staging/prod, env vars, build, deploy, release, domain/DNS, Vercel/cloud/IaaS/PaaS/SaaS/serverless/Docker/container/Kubernetes/DevOps/CI/CD/monitoring
13. CS background: OS, kernel, CPU, memory, cache memory, virtual memory, program/process/processor/thread, data structure, algorithm, function/class/object/instance/OOP, TCP/IP/router/switch/load balancer
14. Confusing pairs: frontend/backend, API/DB, authn/authz, session/cookie/token, library/framework/SDK, function/class/object/instance, program/process/processor, build/deploy/release, commit/push/deploy, local/staging/prod, REST/OpenAPI, SQL/NoSQL, server/serverless, Docker/Kubernetes
15. Copy-ready AI request templates

## Entry format

Use a practical five-line format for each term:

```md
## Term
- 뜻: ...
- 마주치는 순간: ...
- 비개발자식 해석: ...
- AI에게 이렇게 말하기: “...”
- 주의: ...
```

For non-developers, "마주치는 순간" and "AI에게 이렇게 말하기" matter more than abstract precision.

## Tone and density

- Use Korean 존댓말 only if the material is directly for learners. For internal drafting, concise plain Korean is fine.
- Avoid developer-purist explanations. Keep enough technical correctness to prevent bad AI instructions.
- Put advanced CS terms in a separate "깊게 외울 필요는 없지만 멈추면 안 되는 단어" section.
- Prefer concrete visible criteria over abstract business language.
- Include copy-ready prompts. A glossary without reusable prompts is less useful for vibe-coding learners.

## Quality checklist

Before calling the glossary done:

- Does it explain the app flow from button -> frontend -> API -> backend -> DB -> response -> screen update -> deployment?
- Does it cover terminal/CLI/GitHub enough to reduce first-time learner panic?
- Does every term help the learner either instruct AI better or verify output better?
- Are dangerous areas flagged: secrets, API keys, RLS, SSL bypass, deletion, migrations, production deploys?
- Are confusing pairs grouped so the learner can compare them directly?
- Are there ready-to-copy prompts for new feature, tech-stack choice, error fixing, UI fixing, DB design, deploy preflight, limiting AI change scope, and project understanding?
