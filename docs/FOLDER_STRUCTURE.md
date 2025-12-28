# Project Folder Structure

This project follows a strict directory organization to ensure maintainability and AI-agent compatibility.

```
/
├── agent/                  # AI Agent configuration and context
│   ├── rules/              # Specific behavioral rules
│   └── workflow/           # Automated workflows
├── docs/                   # Project documentation (Architecture, API, Manuals)
├── src/                    # Source code
│   ├── backend/            # Python/Node backend services
│   └── frontend/           # Web frontend (HTML/CSS/JS or Framework)
├── agent.md                # Principal Rules file
├── task.md                 # Project Tracking & Definition of Ready
└── README.md               # Entry point
```

## Maintenance

- Do not create random folders in Root.
- Always check `agent/rules` before major refactoring.
