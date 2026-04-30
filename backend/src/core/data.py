# Static Org Structure (Phase 1)
TEAMS = [
    {
        "id": "marketing",
        "name": "Marketing",
        "status": "active",
        "tagline": "Content creation & brand growth",
        "color": "#00F0FF",
        "icon": "Megaphone",
        "agents": [
            {"id": "content_writer", "name": "Content Writer", "role": "Content creation & writing", "icon": "PenLine", "skills": ["blog post", "article", "newsletter", "story", "long-form", "write", "content", "caption", "instagram caption", "social media content", "copy", "text"], "color": "#00F0FF"},
            {"id": "social_publisher", "name": "Social Media Publisher", "role": "Schedule & publish posts to social platforms", "icon": "Send", "skills": ["schedule", "publish", "post timing", "distribution", "social media scheduling", "instagram posting", "linkedin publishing", "facebook posting", "multi-platform distribution", "content scheduling"], "color": "#FF00FF"},
            {"id": "seo_specialist", "name": "SEO Specialist", "role": "Keyword & ranking strategy", "icon": "Search", "skills": ["seo", "keyword", "rank", "meta", "search"], "color": "#00FF88"},
            {"id": "ad_copywriter", "name": "Ad Copywriter", "role": "Performance ad copy", "icon": "Megaphone", "skills": ["ad", "campaign", "copy", "headline", "cta"], "color": "#FFB800"},
            {"id": "analytics_agent", "name": "Analytics Agent", "role": "Insights & reporting", "icon": "BarChart3", "skills": ["analytics", "report", "metrics", "dashboard", "kpi"], "color": "#A78BFA"},
        ],
    },
    {
        "id": "engineering",
        "name": "Engineering",
        "status": "active",
        "tagline": "Build, ship & scale",
        "color": "#00FF88",
        "icon": "Cpu",
        "agents": [
            {"id": "frontend_engineer", "name": "Frontend Engineer", "role": "UI components & flows", "icon": "Code2", "skills": ["frontend", "ui", "react", "component", "css", "page"], "color": "#00F0FF"},
            {"id": "backend_engineer", "name": "Backend Engineer", "role": "APIs & services", "icon": "Server", "skills": ["backend", "api", "endpoint", "service", "database", "schema"], "color": "#00FF88"},
            {"id": "devops_agent", "name": "DevOps Agent", "role": "Deploy & infra", "icon": "Cloud", "skills": ["deploy", "infra", "ci", "cd", "docker", "kubernetes", "pipeline"], "color": "#FFB800"},
            {"id": "qa_agent", "name": "QA Agent", "role": "Testing & quality", "icon": "ShieldCheck", "skills": ["test", "bug", "qa", "quality", "regression", "coverage"], "color": "#FF00FF"},
            {"id": "architect_agent", "name": "Architect Agent", "role": "System design", "icon": "Network", "skills": ["architecture", "design", "system", "scale", "diagram", "tech spec"], "color": "#A78BFA"},
        ],
    },
    {
        "id": "sales",
        "name": "Sales",
        "status": "active",
        "tagline": "Pipeline & revenue",
        "color": "#FFB800",
        "icon": "TrendingUp",
        "agents": [
            {"id": "lead_researcher", "name": "Lead Researcher", "role": "Prospect discovery", "icon": "Telescope", "skills": ["lead", "prospect", "research", "icp", "find customers"], "color": "#00F0FF"},
            {"id": "outreach_agent", "name": "Outreach Agent", "role": "Cold email & DMs", "icon": "Mail", "skills": ["outreach", "cold email", "dm", "sequence", "follow up", "email"], "color": "#FF00FF"},
            {"id": "demo_agent", "name": "Demo Agent", "role": "Product demos", "icon": "Presentation", "skills": ["demo", "walkthrough", "pitch", "presentation"], "color": "#FFB800"},
            {"id": "negotiator_agent", "name": "Negotiator", "role": "Deal closing", "icon": "Handshake", "skills": ["negotiate", "close", "deal", "contract", "discount", "pricing"], "color": "#00FF88"},
            {"id": "crm_agent", "name": "CRM Agent", "role": "Pipeline ops", "icon": "Database", "skills": ["crm", "pipeline", "stage", "forecast", "deal log"], "color": "#A78BFA"},
        ],
    },
    {
        "id": "product",
        "name": "Product",
        "status": "active",
        "tagline": "Discover, define, ship",
        "color": "#A78BFA",
        "icon": "Layers",
        "agents": [
            {"id": "user_researcher", "name": "User Researcher", "role": "Interviews & insights", "icon": "Users", "skills": ["user research", "interview", "insight", "persona", "survey"], "color": "#00F0FF"},
            {"id": "pm_agent", "name": "PM Agent", "role": "Specs & roadmap", "icon": "ClipboardList", "skills": ["spec", "prd", "roadmap", "requirement", "user story", "feature"], "color": "#A78BFA"},
            {"id": "designer_agent", "name": "Designer Agent", "role": "Mockups & flows", "icon": "Palette", "skills": ["design", "mockup", "wireframe", "ui", "ux", "flow"], "color": "#FF00FF"},
            {"id": "roadmap_agent", "name": "Roadmap Agent", "role": "Prioritization", "icon": "ListOrdered", "skills": ["prioritize", "roadmap", "backlog", "rice", "quarter"], "color": "#FFB800"},
            {"id": "feedback_agent", "name": "Feedback Agent", "role": "Synthesize feedback", "icon": "MessageSquare", "skills": ["feedback", "review", "synthesize", "support tickets", "sentiment"], "color": "#00FF88"},
        ],
    },
]

LOCKED_TEAMS = []  # All teams unlocked in this iteration


# Dummy outputs for agent execution simulation
DUMMY_OUTPUTS = {
    # Marketing
    "content_writer": [
        "Content creation completed with engaging copy optimized for target audience.",
        "Written content delivered with proper tone, style, and platform-specific formatting.",
        "Creative content generated with compelling messaging and clear call-to-action.",
    ],
    "social_publisher": [
        "Successfully published to Instagram with optimized hashtags and engagement features.",
        "LinkedIn post published with professional tone and industry-relevant hashtags.",
        "Facebook event created with location details and community engagement features.",
        "Multi-platform distribution completed across Instagram, LinkedIn, and Facebook.",
        "Content scheduled for optimal posting times with platform-specific optimizations.",
        "Social media analytics tracking enabled across all published platforms.",
    ],
    "seo_specialist": [
        "Top 8 keywords identified: 'autonomous agents', 'AI startup OS', 'multi-agent SaaS'. Volume + difficulty mapped.",
        "Meta description + H1 rewritten for target page. Predicted CTR uplift: +18%.",
        "On-page SEO audit complete. 12 fixes proposed, 3 critical (title length, schema, internal links).",
    ],
    "ad_copywriter": [
        "Generated 5 ad variants. Top winner: 'Stop hiring. Start orchestrating.' — CTR-optimized headline.",
        "Performance ad pack ready: 3 headlines, 3 descriptions, 1 hero CTA. Tone: bold, founder-focused.",
        "Campaign copy delivered for Google + Meta. Negative keywords flagged. Budget split recommended.",
    ],
    "analytics_agent": [
        "Last 7-day report: Engagement +24%, Reach +12%, CTR steady. Top channel: LinkedIn.",
        "Funnel analysis: signup form drop-off 38%. Recommendation — simplify to 2 fields.",
        "KPI dashboard refreshed. North-star metric: weekly active orchestrations, +9% WoW.",
    ],
    # Engineering
    "frontend_engineer": [
        "Component shipped: <DashboardCard /> with motion-on-mount, dark-glass surface, 4 variants. 100% test coverage.",
        "Implemented responsive landing hero with parallax. LCP improved 1.8s → 0.9s.",
        "Refactored router to use lazy chunks. Bundle reduced 31%.",
    ],
    "backend_engineer": [
        "API endpoint POST /agents/run shipped. Mongo schema versioned, idempotent retries baked in.",
        "Implemented background worker queue with at-least-once delivery + dead letter pipeline.",
        "Added rate limiter middleware (token bucket, 100 req/min/user).",
    ],
    "devops_agent": [
        "CI/CD pipeline configured. Deploy time: 12m → 3m. Auto-rollback on failed health checks.",
        "Provisioned staging cluster. Cost optimized via spot instances (-42%).",
        "Observability stack rolled out: Grafana + Loki + Tempo. SLO dashboards live.",
    ],
    "qa_agent": [
        "QA pass complete. 14 issues filed (3 critical, 7 medium, 4 minor). Repro steps documented.",
        "End-to-end Playwright suite green. Coverage: 87% across 4 critical user journeys.",
        "Regression sweep done — fixed 2 flakiness sources. Test runtime down 35%.",
    ],
    "architect_agent": [
        "System design ready: event-driven pipeline, fan-out via topic, idempotent consumers. Diagram exported.",
        "Sketched multi-tenant data model with row-level isolation. Migration plan in 4 phases.",
        "Recommended moving to CQRS for read-heavy paths. ROI: 3.2x query throughput.",
    ],
    # Sales
    "lead_researcher": [
        "Identified 47 high-intent prospects matching ICP (Series A SaaS, 50-200 ppl, EU+US). CSV exported.",
        "Built target list of 120 design-led startups with hiring signals last 30 days.",
        "Found 18 lookalike accounts to top 5 customers, scored by fit + reach.",
    ],
    "outreach_agent": [
        "3-step cold email sequence drafted. Personalization tokens for 47 leads. Predicted reply rate: 11%.",
        "LinkedIn outbound DM cadence ready. Mobile-friendly, under 280 chars per touch.",
        "Reactivation email sent to 220 dormant leads. Subject line: 'still on your radar?'",
    ],
    "demo_agent": [
        "20-min demo script prepared. 3 key 'wow' moments. Objection handling for top 5 concerns.",
        "Pitch deck refreshed. Slides cut from 24 → 12. Hero slide: 'work-as-software'.",
        "Recorded 6-min product walkthrough for async sharing. Click-to-action timestamped.",
    ],
    "negotiator_agent": [
        "Term sheet draft ready. Anchored at $48k/yr, with multi-year discount ladder.",
        "Closed deal: 3-year commit, $124k ARR, 2-month ramp. Procurement docs filed.",
        "Counter to procurement: held on price, gave 60-day pilot extension. Risk: low.",
    ],
    "crm_agent": [
        "Pipeline refreshed. 42 deals total — 7 in commit, 12 in best-case. Forecast: $283k this quarter.",
        "Pruned stale deals (>60d no activity). Pipeline accuracy +18%.",
        "Stage analytics: avg time in 'demo done' = 9 days. Bottleneck flagged.",
    ],
    # Product
    "user_researcher": [
        "12 interviews conducted. Top theme: users want 'visible orchestration'. Verbatim quotes attached.",
        "Persona refresh: 3 archetypes (Founder, Ops Lead, IC). Pain map and JTBD updated.",
        "Survey n=314 closed. NPS 58 (+11). Top friction: onboarding step 3.",
    ],
    "pm_agent": [
        "PRD drafted: 'Multi-team orchestration v1'. Scope, constraints, metrics, rollout plan.",
        "User stories for sprint 14 ready. 18 stories, 36 points, dependencies mapped.",
        "Killed 2 features that didn't move north-star. Reallocated 6 dev-weeks.",
    ],
    "designer_agent": [
        "Hi-fi mockups delivered for new dashboard. 3 variants. Tokens added to design system.",
        "Onboarding flow redesigned. Cut 5 → 2 steps. Predicted activation lift: +22%.",
        "Empty-state library shipped. 8 illustrations, on-brand, dark-mode tuned.",
    ],
    "roadmap_agent": [
        "Q-roadmap prioritized via RICE. Top 3: multi-team support, LLM swap, sharing UX.",
        "Backlog groomed. 47 → 22 items. Cut: low-impact infra polish.",
        "Quarterly review deck prepared. 4 themes, 11 commits, 3 stretch goals.",
    ],
    "feedback_agent": [
        "Synthesized 184 support tickets. Top 3 themes: agent picker UX, output export, dark mode polish.",
        "Sentiment trend: +14% positive over last 30 days. Negative concentrated on billing surprises.",
        "Feature request leaderboard updated. Winner: 'export to Notion' (98 votes).",
    ],
}